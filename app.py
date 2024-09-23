import os
import uuid
import mimetypes
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, List
from datetime import datetime, date
from dateutil import parser
import strawberry
from fastapi import FastAPI, status, HTTPException, File, UploadFile, Depends
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from schema import Mutation, Query
from src import models, logger
from src.auth import create_token, get_current_user
from src.crud import authenticate_employee
from src.database import engine, get_db
from src.models import Employee, CompanySettings, Attendance, AttendanceState, AppVersions, UploadedFile
from src.schema.input_type import LoginInput
from src.utils import is_employee_late, run_hasura_mutation, PineconeSigleton, upload_to_s3
from deepface import DeepFace
import boto3

models.Base.metadata.create_all(bind=engine)

s3 = boto3.client(
    's3',
    aws_access_key_id= os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key= os.getenv('AWS_SECRET_KEY'),
    region_name='eu-north-1'  # Optional
)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
schema = strawberry.Schema(mutation=Mutation, query=Query)
pinecone_client = PineconeSigleton()
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

os.makedirs('uploads', exist_ok=True)

@app.get("/")
def greet_json():
    return {"Hello": "World!"}

@app.post("/api/v1/add_employee")
async def create_employee():

    return {"created" : "user"}

@app.post("/api/v1/login")
async  def login(user: LoginInput):
    with next(get_db()) as db:
        employee_with_role = authenticate_employee(db, user.phone_number, user.password)
        try:
            if employee_with_role:
                token = create_token(employee_with_role)
                return {
                    "employee": employee_with_role,
                    "token": token
                }
            else:
                raise  HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect phone number or password")
        except Exception as e:
            logger.exception(e)
            db.rollback()
            db.close()
            raise e
        finally:
            db.close()

@app.post("/api/v1/attendance-trigger")
async def attendance_trigger(body: Dict):
    employee_id = body['event']['data']['new']['employee_id']
    inserted_attendance = body['event']['data']['new']
    print(inserted_attendance)

    with next(get_db()) as db:
        try:
            # Get employee and company settings
            employee = db.query(Employee.company_id).filter(Employee.id == employee_id).first()
            company_settings = db.query(CompanySettings).filter(
                CompanySettings.company_id == employee.company_id
            ).first()

            # Parse clock-in time
            clock_in_time_unformatted = parser.isoparse(inserted_attendance['clock_in_time'])
            clock_in_time = clock_in_time_unformatted.time().strftime('%H:%M:%S')

            start_work_time = company_settings.start_work_time
            max_late_time = company_settings.max_late_time

            # Check if the employee is late
            is_late = is_employee_late(clock_in_time, start_work_time, max_late_time)

            attendance_state = AttendanceState(
                is_late = is_late,
                attendance_id = inserted_attendance["id"]
            )
            db.add(attendance_state)
            db.commit()

        except Exception as e:
            logger.exception(e)
            db.rollback()
            db.close()
            raise e
        finally:
            db.close()


    return {"message" : "Received and printed"}


@app.post("/api/v1/profile")
async def insert_face(
    face: UploadFile = File(...),
    user: str = Depends(get_current_user),
    ):
    today = date.today()

    try:
        image_path = f"uploads/{face.filename}"
        
        with open(image_path, "wb") as f:
            f.write(await face.read())
        mime_type, _ = mimetypes.guess_type(image_path)
        file_size = os.path.getsize(image_path)
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")
    try:
        file_url = upload_to_s3(
            s3_file=str(uuid.uuid4()),
            s3=s3,
            local_file=image_path,
            bucket_name='vvims-visitor'
        )
        print("File url", file_url)
    except Exception as e:
        logger.exception(e)

    with next(get_db()) as db:
        try:
            file = UploadedFile(
                file_name = f"{face.filename}",
                file_url = file_url,
                mime_type = f"{mime_type}",
                file_size = (file_size/1024)
            )
            db.add(file)
            db.commit()
            employee = db.query(Employee).filter(Employee.id == user).first()
            employee.profile_picture = file.id
            db.commit()
        except Exception as e:
            logger.exception(e)
            db.rollback()
            db.close()
            raise e
        finally:
            db.close()

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Face image uploaded", "file_url": file_url})

    # try:
    #     embeddings = DeepFace.represent(img_path=image_path, model_name="VGG-Face", enforce_detection=False)
    #     embedding = embeddings[0]["embedding"]
    #     result =  pinecone_client.insert(
    #         embedding = embedding,
    #         firstname = firstname,
    #         # lastname = lastname,
    #         # phone_number = phone_number,
    #         date= str(today.strftime('%B %d, %Y'))
    #     )
    #     return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Face image uploaded"})
    # except Exception as e:
    #     logger.exception(e)
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"{str(e)}")

@app.post("/api/v1/upload-app")
async def upload_app(name: str, version: str, app: UploadFile = File(...)):
    try:
        file_path = f"uploads/app"
        mime_type, _ = mimetypes.guess_type(file_path)
        file_size = os.path.getsize(file_path)
        with open(file_path, "wb") as f:
            f.write(await app.read())
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")
    try:
        file_url = upload_to_s3(
            s3_file=str(uuid.uuid4()),
            s3=s3,
            local_file=file_path,
            bucket_name='vvims-visitor'
        )
    except Exception as e:
        logger.exception(e)

    with next(get_db()) as db:
        try:
            app_version = AppVersions(
                version = version,
                name = name,
                url = file_url
            )
            db.add(app_version)
            db.commit()
        except Exception as e:
            logger.exception(e)
            db.rollback()
            db.close()
            raise e
        finally:
            db.close()

@app.get("/api/v1/upload-app/")
async def get_app():
    with next(get_db()) as db:
        try:
            app_version = db.query(AppVersions).order_by(AppVersions.version.desc()).first()
            return app_version
        except Exception as e:
            db.rollback()
            db.close()
            logger.exception(e)
        finally:
            db.close()


@app.post("/recognize")
async def recognize(
    embedding: List[float],
    ):

    matches = pinecone_client.query(embedding)

    serialized_vectors = []
    for vec in matches:
        serialized_vectors.append({
            "id": vec.get("id"),
            "score": vec.get("score"),
            "metadata" : vec.get("metadata")
        })
    print(serialized_vectors)
    if(serialized_vectors[0]["score"] >= 0.79):
        return JSONResponse(status_code=status.HTTP_200_OK, content={"matches": serialized_vectors[0]})
    return JSONResponse(status_code=status.HTTP_400_NOT_FOUND, content={"matches": [], "message": "Intruder visitor did not regidter today"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)