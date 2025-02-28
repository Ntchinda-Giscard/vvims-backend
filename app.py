import random
from reportlab.pdfgen import canvas
import os
import io
from typing import Optional, Any
import uuid
import mimetypes
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Dict, List, Optional
from datetime import datetime, date
from dateutil import parser
import strawberry
from fastapi import FastAPI, status, HTTPException, File, UploadFile, Depends, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from schema import Mutation, Query, Subscription
from src import models, logger
from src.auth import create_token, get_current_user
from src.crud import authenticate_employee, get_employee_attendance_summary, get_department_attendance_summary, attendance_percentage, average_time_in_office, average_compnay_arrival_time, get_company_name
from src.database import engine, get_db
from src.models import Employee, CompanySettings, Department, Attendance, AttendanceState, AppVersions, UploadedFile, Company, TextContent,\
    EmployeeNotification, Visit, Visitor, EmployeeNotificationType, EventParticipant, ParticipantStatus, Conversation, \
    EmployeeConversation, Attachment, Message, MessageStatus, MessageStatuses, \
    Report, ReportTypes
from src.schema.input_type import LoginInput
from src.utils import (
    is_employee_late, PineconeSigleton, upload_to_s3, generate_date_range, get_attendance_for_day,
    calculate_time_in_building, LocalUploadStrategy, S3UploadStrategy, UploadProcessor, UploadStrategies,
    ReportService, ChromaService
)
import boto3
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from zoneinfo import ZoneInfo
from src.utilities import generate_pdf
from src.components.reports import (
    ReportGeneratorContext, upload_report_to_s3
    )
from src.components.reports import ReportType, ReportName
from src.schema.input_type import (
    ReportRequest,
    ReportTypes,
    CategoryType
)

import asyncio
from deepface import DeepFace



models.Base.metadata.create_all(bind=engine)
server_instance = os.getenv('SERVER_INSTANCE'),
s3 = boto3.client(
    's3',
    aws_access_key_id= os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key= os.getenv('AWS_SECRET_KEY'),
    region_name='eu-north-1'
)

app = FastAPI(
    swagger_ui_init_oauth=None,  # Disables the online CDN for OAuth2 redirect URL
    swagger_ui_parameters={"useBaseUrl": True}  # Forces using local base URL for assets
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
schema = strawberry.Schema(mutation=Mutation, query=Query, subscription=Subscription)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# pinecone_client = PineconeSigleton()
UPLOAD_DIR = '/app/uploads'
os.makedirs('/uploads', exist_ok=True)

app.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

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
        # employee_with_role.firebase_token = user.firebase_token if user.firebase_token else employee_with_role.firebase_token
        # db.commit()
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

@app.post("/api/v1/visit-trigger")
async def visits_trigger(body: Dict):
    print(body)
    data = body['event']['data']['new']
    with next(get_db()) as db:
        try:

            db_visitor = db.query(Visitor).filter(Visitor.id == data["visitor"]).first()

            print(f"Host employee ========>  {data['host_employee']}")
            db_notif = EmployeeNotification(
                employee_id = data["host_employee"],
                action = "New Visitor",
                type = EmployeeNotificationType.VISITS,
                title = "New Visitor Alert !",
                message=f"{db_visitor.firstname} {db_visitor.lastname} is paying you a visit!",
                visits_id = data['id'],
                is_read = False
            )

            print(f"Notification info: Employee: {db_notif.employee_id}, message: {db_notif.message}")
            db.add(db_notif)
            db.commit()

        except Exception as e:
            db.rollback()
            db.close()
            logger.exception(e)
        finally:
            db.close()
    return {"message": "Event triggered"}


@app.post("/api/v1/events-trigger")
async def events_trigger(body: Dict):
    print(body['event']['data']['new'])

    event_id = body['event']['data']['new']['id']
    event_data = body['event']['data']['new']
    print("event id", event_id)

    # Open the session once
    with next(get_db()) as db:
        try:
            # Query participants of the event
            event_participants = db.query(EventParticipant).filter(EventParticipant.event_id == event_id).all()
            print("event participants", event_participants)

            # Process each participant
            for participant in event_participants:
                participant.status = ParticipantStatus.PENDING
                db_notif = EmployeeNotification(
                    action="New events alert !",
                    title=event_data['title'],
                    message=event_data['description'],
                    is_read=False,
                    type=EmployeeNotificationType.EVENTS,
                    employee_id=participant.employee_id,
                    event_id = participant.event_id
                )

                db.add(db_notif)

            # Commit all notifications in one transaction
            db.commit()
        except Exception as e:
            # Rollback on error
            db.rollback()
            logger.exception(e)
        finally:
            # Close the session at the end
            db.close()


@app.post("/api/v1/message-trigger")
async def message_trigger(body: Dict):
    icon_attachment = {
        'DOCUMENT' : '📄',
        'VOICE' : '🎤',
        'IMAGE' : '🏞',
        'AUDIO' : '🎵',
        'VIDEO' : '🎥'
    }
    message_id = body['event']['data']['new']['id']
    message_data = body['event']['data']['new']
    conv_id = message_data['conversation_id']
    print('message id', message_data)

    with next(get_db()) as db:
        try:
            receiver_id = (
                db.query(EmployeeConversation.employee_id)
                .filter((EmployeeConversation.conversation_id == conv_id) & (EmployeeConversation.employee_id != message_data['sender_id']))
                .scalar()
            )
            attachment = (
                db.query(Attachment)
                .join(Message, Attachment.message_id == message_id)
                .first()
            )
            sender = (
                db.query(Employee)
                .filter(Employee.id == message_data['sender_id'])
                .first()
            )

            message_status = MessageStatus(
                employee_id = message_data['sender_id'],
                status = MessageStatuses.SENT,
                message_id = message_data['id'],
            )
            db.add(message_status)
            if attachment:
                if message_data['content'] != None:
                    icon = f"{attachment.file_type}"
                    content = message_data['content']
                    print('content messages with no content  ======>', content)
                    message = f"{icon_attachment[icon]} {content}"
                else:
                    icon = f"{attachment.file_type}"
                    content = attachment.file_type.capitalize()
                    print('content messages with no content  ======>', content)
                    message = f"{icon_attachment[icon]} {content}"
            else:
                message = message_data['content']

            notification = EmployeeNotification(
                action="New message!",
                title= f"{sender.firstname} {sender.lastname}",
                message= message,
                is_read=False,
                type=EmployeeNotificationType.MESSAGES,
                employee_id = receiver_id,
                message_id= message_id
            )

            db.add(notification)
            db.commit()
        except Exception as e:
            logger.exception(e)
            raise Exception(f'Internal server error: {e}')
        finally:
            db.close()


@app.post("/api/v1/visits-trigger")
async def visit_trigger(body: Any):
    print('Body', body)

    with next(get_db()) as db:
        try:
            print('Body', body)

        except Exception as e:
            logger.exception(e)
            raise Exception(f"Internal server error: {e}")
        finally:
            db.close()

async def upload_files(upload_type: Optional[str]='online', file: UploadFile=File(...)):
    strategies = UploadStrategies( local=LocalUploadStrategy, online=S3UploadStrategy)

    processor = UploadProcessor(strategies)
    result = await processor.process(upload_type, file)
    print(result)

    return result

@app.post("/api/v1/profile")
async def insert_face(
    upload_type: Optional[str],
    face: UploadFile = File(...),
    user: str = Depends(get_current_user)

    ):
    today = date.today()


    try:

        result = await upload_files(upload_type, face)
        print("File url", result)
    except Exception as e:
        logger.exception(e)

    with next(get_db()) as db:
        try:
            file = UploadedFile(
                # file_name = f"{face.filename}",
                file_name = "",
                file_url = result,
                mime_type = "",
                file_size = 0
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

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "Face image uploaded", "file_url": result})

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
async def upload_app(name: str, version: str, apps: UploadFile = File(...)):
    try:
        file_path = f"uploads/app"
        # mime_type, _ = mimetypes.guess_type(file_path)
        # file_size = os.path.getsize(file_path)
        with open(file_path, "wb") as f:
            f.write(await apps.read())
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail=f"{str(e)}")
    try:
        file_url = upload_to_s3(
            s3_file=str(uuid.uuid4()) + ".apk",
            s3=s3,
            local_file=file_path,
            bucket_name='vvims-visitor'
        )
    except Exception as e:
        logger.exception(e)
        raise e

    with next(get_db()) as db:
        try:
            app_version = AppVersions(
                version = version,
                name = name,
                url = file_url
            )
            db.add(app_version)
            db.commit()
            if file_url:
                return {"message": "Upload successful", "file_url": file_url}
            else:
                return {"message": "Upload failed"}
        except Exception as e:
            logger.exception(e)
            db.rollback()
            db.close()
            raise e
        finally:
            db.close()

async def uploads_save(file: UploadFile, upload_type: Optional[str]):

    file_path = f"uploads/{file.filename}"

    # Asynchronously read and save the file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    strategies = UploadStrategies(local=LocalUploadStrategy, online=S3UploadStrategy)

    processor = UploadProcessor(strategies)
    file_url = await processor.process(upload_type, file)

    # Determine the MIME type and file size
    mime_type, _ = mimetypes.guess_type(file_path)
    file_size = os.path.getsize(file_path)


    return mime_type, file_size, file_url, file.filename, file_path

@app.post("/api/v1/upload-file")
async def upload_file_strategy(upload_type: Optional[str]='online', file: UploadFile=File(...)):
    # strategies = UploadStrategies()
    strategy = UploadStrategies[upload_type]

    # processor = UploadProcessor(strategies)
    result = await strategy.upload_process(file)
    print(result)

    return {"file_url" : result}



def sanitize_none(value: Optional[str]) -> str:
    """Convert None to an empty string to avoid JSON errors."""
    return value or ""


@app.post("/api/v1/add-visits")
async def add_visit_with_visitor(
        upload_type: Optional[str],
        firstname: Optional[str] = Form(None),
        lastname: Optional[str] = Form(None),
        phone_number: Optional[str] = Form(None),
        id_number: Optional[str] = Form(None),
        host_employee: Optional[uuid.UUID] = Form(None),
        host_department: Optional[uuid.UUID] = Form(None),
        host_service: Optional[uuid.UUID] = Form(None),
        vehicle: Optional[uuid.UUID] = Form(None),
        visitor: Optional[uuid.UUID] = Form(None),
        status: str = Form("PENDING"),
        reason: str = Form(...),
        reg_no: Optional[str] = Form(None),
        face: UploadFile = File(None),
        front_id: Optional[str] = Form(None),
        back_id: Optional[str] = Form(None),
        # user: str = Depends(get_current_user),
    ):
    if not host_employee and not host_service and not host_department:
        raise HTTPException(status_code=400, detail="Bad request. Missing one of these: Department, service and employee") 
    if face:
        # Use 'await' to call the asynchronous 'uploads_save' function
        mime_type = ''
        file_size = 0
        face_file_url = ''
        face_file_name = ''
        try:
            mime_type, file_size, face_file_url, face_file_name, file_path = await uploads_save(face, upload_type=upload_type)
            print(f"type=={mime_type}, size=={file_size}, url=={face_file_url}, filename=={face_file_name}, path=={file_path}")
            embedding_objs = DeepFace.represent(
                img_path= file_path
            )
            embedding = embedding_objs[0]["embedding"]

        except Exception as e:
            pass
        print(mime_type, file_size, face_file_url, face_file_name)
    # Database operations (rest of the logic stays the same)
    with next(get_db()) as db:
       
        if face:
            try:
                db_face = UploadedFile(
                    file_name=face_file_name,
                    file_url=face_file_url,
                    mime_type= mime_type,
                    file_size = file_size
                )
                db.add(db_face)
                db.commit()
            except Exception as e:
                logger.exception(e)
                db.rollback()
                raise HTTPException(status_code=500, detail=str(e))

        if front_id:
            try:
                db_front = UploadedFile(
                    file_name= face_file_name,
                    file_url=face_file_url,
                    mime_type=mime_type,
                    file_size=file_size
                )
                db.add(db_front)
                db.commit()
            except Exception as e:
                logger.exception(e)
                db.rollback()
                raise HTTPException(status_code=500, detail=str(e))

        if back_id:
            try:
                db_back = UploadedFile(
                    file_name=face_file_name,
                    file_url=face_file_url,
                    mime_type=mime_type,
                    file_size=file_size
                )
                db.add(db_back)
                db.commit()
            except Exception as e:
                logger.exception(e)
                db.rollback()
                raise HTTPException(status_code=500, detail=str(e))



        try:
            if visitor:
                db_visits = Visit(
                    host_employee=host_employee,
                    host_department=host_department,
                    host_service=host_service,
                    visitor=visitor,
                    vehicle=vehicle,
                    status=sanitize_none(status),
                    reason=sanitize_none(reason),
                    reg_no=sanitize_none(reg_no),
                )
                db.add(db_visits)
                db.commit()
                return JSONResponse(status_code=200, content={"visit": str(db_visits.id)})
            
            elif not visitor and (firstname or lastname or phone_number or id_number):
                metadata = {
                    "firstname": firstname,
                    "lastname": lastname
                }
                chroma_service = ChromaService()
                chroma_service.insert(
                    embedding = embedding,
                    metadata = metadata,
                    doc = f"This is the face image of {firstname} {lastname}"
                )
                db_visitor = Visitor(
                    firstname=firstname,
                    lastname=lastname,
                    id_number=id_number,
                    phone_number=phone_number,
                    photo=db_face.id if face else None,
                    front_id=db_front.id if front_id else None,
                    back_id=db_back.id if back_id else None
                )
                db.add(db_visitor)
                db.commit()

                db_visit = Visit(
                    host_employee=host_employee,
                    host_department=host_department,
                    host_service=host_service,
                    visitor=db_visitor.id,
                    vehicle=vehicle,
                    status=sanitize_none(status),
                    reason=sanitize_none(reason),
                    reg_no=sanitize_none(reg_no),
                )
                db.add(db_visit)
                db.commit()
                return JSONResponse(status_code=200, content={"visitor": str(db_visitor.id)})
        except Exception as e:
            logger.exception(e)
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))



@app.get("/api/v1/get-app/")
async def get_app():
    with next(get_db()) as db:
        try:
            app_version = db.query(AppVersions).order_by(AppVersions.created_at.desc()).first()
            print(app_version)
            return app_version
        except Exception as e:
            db.rollback()
            db.close()
            logger.exception(e)
        finally:
            db.close()


@app.get("/api/v1/get-datetime/")
async def get_datetime():
    wat_time = datetime.now(ZoneInfo("Africa/Lagos"))
    formated_time = wat_time.strftime("%Y-%m-%d %H:%M:%S")
    return {"datetime": formated_time}

# @app.post("/api/v1/upload-file")
# async def upload_app(file: UploadFile = File(...)):
#     try:
#         file_path = f"uploads/file"
#         # mime_type, _ = mimetypes.guess_type(file_path)
#         # file_size = os.path.getsize(file_path)
#         with open(file_path, "wb") as f:
#             f.write(await file.read())
#     except Exception as e:
#         logger.exception(e)
#         raise HTTPException(status_code=500, detail=f"{str(e)}")
#     try:
#         file_name = str(uuid.uuid4())
#         file_url = upload_to_s3(
#             s3_file=str(file.filename),
#             s3=s3,
#             local_file=file_path,
#             bucket_name='vvims-visitor'
#         )
#         print(file_name)
# 
#         return {"file_url" : file_url}
#     except Exception as e:
#         logger.exception(e)


@app.post("/api/v1/get-attendance/")
async def get_attendance_by_date_range(start_date, end_date):
    date_range = list(generate_date_range(start_date, end_date))
    result = {}
    with next(get_db()) as db:
        for date in date_range:
            print(f"\nDate: {date.strftime('%Y-%m-%d')}")
            
            attendances = get_attendance_for_day(db, date)
            attend = []
            if attendances:
                for attendance in attendances:
                    employee_name = attendance.employee.firstname
                    clock_in = attendance.clock_in_time.strftime("%H:%M:%S")
                    clock_out = attendance.clock_out_time.strftime("%H:%M:%S") if attendance.clock_out_time else None
                    time_spent = calculate_time_in_building(clock_in, clock_out)
                    attend.append([employee_name, clock_in, clock_out, time_spent])
                    
                    print(f"Employee: {employee_name}, Arrived: {clock_in}, Left: {clock_out}, Time in Building: {time_spent}")
            else:
                print("No employees were present.")
            result[date] = attend
        return result


@app.get("/api/v1/get-attendace-report")
async def get_attendace_pdf_reports():
    summary = {}
    with next(get_db()) as db:
        try:
            result = get_employee_attendance_summary(db, Employee, Attendance)
            result_dept = get_department_attendance_summary(db, Department)

            # Company anme
            company_name = get_company_name(db, Company, TextContent)

            # Summary of Company
            summary["arrival_time"] = average_compnay_arrival_time(db, Attendance)
            summary["avr_office_hours"] = average_time_in_office(db, Attendance)
            summary["overall_perc"] = "{:.1f}%".format(attendance_percentage(db, Attendance, Employee))

            pdf_bytes = generate_pdf(result, result_dept, summary, company_name)
            pdf_buffer = io.BytesIO(pdf_bytes)
            # Generate the current timestamp and a random number
            now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
            random_number = str(random.randint(1, 99999)).zfill(5)

            s3.upload_fileobj(pdf_buffer, "vvims-visitor", f"attendance_report_{now}_{random_number}.pdf")
            s3_url = f"https://vvims-visitor.s3.eu-north-1.amazonaws.com/attendance_report_{now}_{random_number}.pdf"

            types = ReportTypes.ATTENDANCE
            report = Report(
                report_link=s3_url,
                types = types,
                from_date = datetime.now(),
                to_date = datetime.now(),
                name = "Attendance Report"
            )

            db.add(report)
            db.commit()
            print(f"Observation {s3_url}")
            return {"pdf_url": s3_url}
            # return result
        except Exception as e:
            raise e
        finally:
            db.close()


@app.get("/api/v1/get-report")
async def get_pdf_report(report_type: str):
    report_strategy = ReportType.get(report_type)
    if not report_strategy:
        return {"error": "Invalid report type"}
    report_context = ReportGeneratorContext(report_strategy)
    pdf_report = report_context.generate_report()
    s3_url = upload_report_to_s3(pdf_report)
    with next(get_db()) as db:
        
        report_name = ReportName[report_type]
        types = { "attendance" : ReportTypes.ATTENDANCE,
        "visit" : ReportTypes.VISITS,
        "task" : ReportTypes.TASKS }
        report = Report(
            report_link=s3_url,
            types = types[report_type],
            from_date = datetime.now(),
            to_date = datetime.now(),
            name = report_name
        )
        db.add(report)
        db.commit()
    return {"pdf_url": s3_url}


@app.post("/api/v1/get-reports")
async def get_pdf_reports(
    request: ReportRequest
    ):
    report_service = ReportService()
    data, pdf_bytes = await report_service.generate_report(request)
    report_name = ReportName[request.report_type]
    s3_url = upload_report_to_s3(pdf_bytes, report_name)
    with next(get_db()) as db:
        
        

        report = Report(
            report_link=s3_url,
            types = request.report_type,
            from_date = datetime.now(),
            to_date = datetime.now(),
            name = report_name
        )
        db.add(report)
        db.commit()

    return {"s3_url": s3_url}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)