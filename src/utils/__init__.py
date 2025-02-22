from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from fastapi import UploadFile, File, HTTPException
from abc import abstractmethod, ABC
from sqlalchemy import and_
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timedelta, time, date
import requests
from pinecone import Pinecone
from botocore.exceptions import NoCredentialsError
import google.auth
from google.oauth2 import service_account
import google.auth.transport.requests
from src import logger
from src.models import Attendance, Employee
from src.schema.input_type import ReportTypes, CategoryType, ReportRequest
from src.database import engine, get_db
import boto3
import os

UPLOAD_DIR = '/app/uploads'

s3 = boto3.client(
    's3',
    aws_access_key_id= os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key= os.getenv('AWS_SECRET_KEY'),
    region_name='eu-north-1'
)

def auth_firebase_token() -> str:
    SERVICE_ACCOUNT_FILE= './vvims-emplo-firebase-adminsdk-sg73f-d935f36b7e.json'

    SCOPES=['https://www.googleapis.com/auth/firebase.messaging']

    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

    request =google.auth.transport.requests.Request()
    credentials.refresh(request)
    access_token = credentials.token
    print(access_token)
    return access_token


def is_employee_late(clock_in_time, start_work_time, max_late_time: timedelta) -> bool:
    # Convert clock_in_time to datetime.time if it's a string
    if isinstance(clock_in_time, str):
        clock_in_time = datetime.strptime(clock_in_time, "%H:%M:%S").time()

    # Convert start_work_time to datetime.time if it's a string
    if isinstance(start_work_time, str):
        start_work_time = datetime.strptime(start_work_time, "%H:%M:%S").time()

    # Combine start work time with today's date
    start_work_datetime = datetime.combine(datetime.today(), start_work_time)

    # Add max late time (timedelta) to start work time
    max_allowed_time = start_work_datetime + max_late_time

    # Combine clock in time with today's date
    clock_in_datetime = datetime.combine(datetime.today(), clock_in_time)

    # Check if the employee is late
    return clock_in_datetime > max_allowed_time

def enforce_date(value):
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Incorrect date format, should be YYYY-MM-DDD")
    elif isinstance(value, datetime):
        return value
    else:
        raise TypeError("Expected string or datetime object")

def generate_date_range(start_date, end_date):
    start_date = enforce_date(start_date)
    end_date = enforce_date(end_date)

    current_date = start_date

    while current_date <= end_date:
        yield current_date
        current_date += timedelta(days=1)

def calculate_time_in_building(clock_in, clock_out):
    fmt = "%H:%M:%S"
    if clock_out :
        clock_in = datetime.strptime(clock_in, fmt)
        clock_out = datetime.strptime(clock_out, fmt)

        if clock_out > clock_in:
            return clock_out - clock_in
        elif clock_in > clock_out:
            return datetime.strptime("15:00:00", fmt) - clock_in
    return None

def get_attendance_for_day(db, date):
    # Query attendance for a specific date (filtering on clock_in date only)
    return db.query(Attendance).join(Employee).filter(
        and_(
            Attendance.clock_in_time >= date,
            Attendance.clock_in_time < date + timedelta(days=1)
        )
    ).all()

def run_hasura_mutation(mutation, variables, url, admin_secret):
    """
    Execute a GraphQL mutation against a Hasura instance.
    Args:
        mutation (str): The GraphQL mutation query as a string.
        variables (dict): A dictionary of variables to pass to the mutation.
        url (str): The Hasura GraphQL endpoint URL.
        admin_secret (str): The Hasura admin secret for authentication.
    Returns:
        dict: The response from Hasura, either the result of the mutation or an error.
    """

    headers = {
        "Content-Type": "application/json",
        "x-hasura-admin-secret": admin_secret
    }

    data = {
        "query": mutation,
        "variables": variables
    }

    # Send the POST request
    response = requests.post(url, json=data, headers=headers)

    # Return the response as a JSON object
    return response.json()


class PineconeSigleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PineconeSigleton, cls).__new__(cls, *args, **kwargs)
            cls._instance.pinecone_client = Pinecone(api_key="dc53a991-1d1a-4f03-b718-1ec0df3b0f00")
            cls._instance.index = cls._instance.pinecone_client.Index("faces-id")
        return cls._instance

    def insert(self, embedding, firstname="", lastname="", phone_number="", date=""):
        self.index.upsert(vectors=[
            {
                "id": str(uuid.uuid4()),
                "values": embedding,
                "metadata": {"firstname": firstname, "lastname": lastname, "phone_number": phone_number, "date": date},
            }],
            namespace="ns1"
        )

    def query(self, embedding, top_k=1):
        today = date.today()
        matches = self.index.query(
            namespace="ns1",
            vector=embedding,
            top_k=top_k,
            include_values=False,
            include_metadata=True,
            filter={"date": {"$eq": str(today.strftime('%B %d, %Y'))}}
        )

        print(matches["matches"])

        return matches["matches"]



def upload_to_s3(local_file, bucket_name, s3_file, s3, is_apk=False):
    try:
        # Upload the file to S3
        s3.upload_file(local_file, bucket_name, s3_file)
        print(f'Successfully uploaded {local_file} to {bucket_name}/{s3_file}')

        # Construct the file's URL
        location = s3.get_bucket_location(Bucket=bucket_name)['LocationConstraint']
        file_url = f"https://{bucket_name}.s3.{location}.amazonaws.com/{s3_file}"

        return file_url

    except FileNotFoundError:
        print(f'The file {local_file} was not found.')
        return None
    except NoCredentialsError:
        print('Credentials not available.')
        return None


class UploadStrategy(ABC):

    @abstractmethod
    async def upload_process(self, file: UploadFile = File(...)) -> str:
        pass

class S3UploadStrategy(UploadStrategy):

    async def upload_process(self, file: UploadFile = File(...)) -> str:
        try:
            file_path = f"uploads/file"
            # mime_type, _ = mimetypes.guess_type(file_path)
            # file_size = os.path.getsize(file_path)
            with open(file_path, "wb") as f:
                f.write(await file.read())
        except Exception as e:
            logger.exception(e)
            raise HTTPException(status_code=500, detail=f"{str(e)}")
        try:
            file_name = str(uuid.uuid4())
            file_url = upload_to_s3(
                s3_file=str(file.filename),
                s3=s3,
                local_file=file_path,
                bucket_name='vvims-visitor'
            )
            print(file_name)

            return f"{file_url}"
        except Exception as e:
            logger.exception(e)


class LocalUploadStrategy(UploadStrategy):

    async def upload_process(self, file: UploadFile = File(...)) -> str:
        try:
            folder = Path(UPLOAD_DIR) / file.filename

            with open(folder, "wb") as f:
                f.write(await file.read())

            return  f"http://172.17.15.28:30088/uploads/{file.filename}"
        except Exception as e:
            logger.exception(e)
            raise e


@dataclass
class UploadStrategies:
    online: Callable[[], UploadStrategy]
    local: Callable[[], UploadStrategy]

    def get_strategy(self, upload_type: str) -> UploadStrategy:
        """
        Dynamically fetch the correct strategy based on client input
        """

        strategy_creator = getattr(self, upload_type, None)
        if not strategy_creator:
            raise ValueError(f"Unsupported upload type: {upload_type} ")
        strategy_instance = strategy_creator()
        if not isinstance(strategy_instance, UploadStrategy):
            raise TypeError(f"Strategy is not of type UploadStrategy: {strategy_instance}")

        return strategy_instance

class UploadProcessor:

    def __init__(self, strategy: UploadStrategies):
        self.strategies = strategy

    async def process(self, upload_type: str, file: UploadFile=File(...)) -> str:

        strategy = self.strategies.get_strategy(upload_type)
        result  = await strategy.upload_process(file=file)

        return result


class ReportGenerator(ABC):
    async def generate(self, filter_by: CategoryType, filter_id: uuid.UUID, start_date: datetime, end_date: datetime):

        return NotImplementedError

class VisitReportGenerator(ReportGenerator):
    async def generate(self, filter_by: CategoryType, filter_id: uuid.UUID, start_date: datetime, end_date: datetime):
        sql_query = self._build_query(filter_by)
        async with next(get_db()) as db:
            result = await db.execute(sql_query,{
                "filter_id" : 
            })
    
    def _build_query(self, filter_by: CategoryType) -> str:
        base_query = """
            SELECT 
                vi.date, 
                vi.check_in_at, 
                vi.reason, 
                v.firstname, 
                v.lastname
        """
        
        if filter_by == CategoryType.EMPLOYEE:
            return base_query + """
                    FROM visits AS vi
                    JOIN visitors AS v ON vi.visitor = v.id
                    WHERE vi.host_employee = :filter_id
                    AND vi.date BETWEEN :start_date AND :end_date
                    ORDER BY vi.date;
            """
        
        elif filter_by == CategoryType.SERVICE:
            return base_query + """
                    FROM visits AS vi
                    JOIN visitors AS v ON vi.visitor = v.id
                    WHERE vi.host_service = :filter_id
                    AND vi.date BETWEEN :start_date AND :end_date
                    ORDER BY vi.date;
                """
        elif filter_by == CategoryType.DEPARTMENT:
            return base_query + """ 
                    FROM visits AS vi
                    JOIN departments AS d ON vi.host_department = d.id
                    JOIN visitors AS v ON vi.visitor = v.id
                    WHERE d.id = :filter_id
                    AND vi.date BETWEEN :start_date AND :end_date
                    ORDER BY vi.date;
                """


class AttendanceReportGenerator(ReportGenerator):
    
    async def generate(self, filter_by: CategoryType, filter_id: uuid.UUID, start_date: datetime, end_date: datetime):

        return -1
    
    def _build_query(self, filter_by: CategoryType) -> str:

        base_query = """
        """



class ReportService:

    def __init__(self, db):
        self.db = db
        self.generators = {
            ReportTypes.VISIT: VisitReportGenerator(),
            ReportTypes.ATTENDANCE: AttendanceReportGenerator()
        }
    
    async def generate_report(self, request: ReportRequest) -> dict:

        end_date = request.end_date or datetime.nom()
        start_date = request.start_date or (end_date - timedelta(days=30))

        generator = self.generators[request.report_type]

        data  = await generator.generate(
            request.filter_by,
            start_date,
            end_date
        )