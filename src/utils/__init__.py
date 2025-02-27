from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from fastapi import UploadFile, File, HTTPException
from abc import abstractmethod, ABC
from sqlalchemy import and_, text
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
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os
import asyncio
from typing import Dict, List
from collections import Counter
from typing import Any
from chromadb import Client


env = Environment(loader=FileSystemLoader("template"))
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
        print(f"Filter by ====> {filter_by}")
        print(f"Query built ====> {sql_query}")
        with next(get_db()) as db:
            results = db.execute(text(sql_query),{
               "filter_id" : filter_id,
               "start_date" : start_date,
               "end_date" : end_date
           }).mappings().all()
        # return [dict(zip(row.keys(), row)) for row in results]
        return results
    
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
                    JOIN visitors AS v ON vi.visitor = v.id
                    WHERE vi.host_department = :filter_id
                    AND vi.date BETWEEN :start_date AND :end_date
                    ORDER BY vi.date;
                """


class AttendanceReportGenerator(ReportGenerator):
    
    async def generate(self, filter_by: CategoryType, filter_id: uuid.UUID, start_date: datetime, end_date: datetime):

        sql_query = self._build_query(filter_by)
        with next(get_db()) as db:
            results = db.execute(text(sql_query), {
               "filter_id" : filter_id,
               "start_date" : start_date,
               "end_date" : end_date
           }).mappings().all() 

        # return [dict(zip(row.keys(), row)) for row in results]
        return results
    
    def _build_query(self, filter_by: CategoryType) -> str:

        base_query = """
        SELECT att.clock_in_date, att_state.is_late, att.clock_out_time, att.clock_in_time, e.firstname, e.lastname,
            EXTRACT(EPOCH FROM (att.clock_out_time - att.clock_in_time))/3600 AS hours_worked
        FROM attendance as att
        JOIN attendance_state AS att_state ON att.id = att_state.attendance_id
        JOIN employees as e ON e.id = att.employee_id
        """

        if filter_by == CategoryType.EMPLOYEE:
            return base_query + """
                WHERE att.employee_id = :filter_id
                AND att.clock_in_date BETWEEN :start_date AND :end_date
                ORDER BY att.clock_in_date;
            """
        elif filter_by == CategoryType.SERVICE:
            return base_query + """
                
                JOIN services as s ON e.service_id = s.id
                WHERE s.id = :filter_id
                AND att.clock_in_date BETWEEN :start_date AND :end_date
                ORDER BY att.clock_in_date;
            """
        
        elif filter_by == CategoryType.DEPARTMENT:
            return base_query + """
                JOIN departments as d ON e.department_id = d.id
                WHERE d.id = :filter_id
                AND att.clock_in_date BETWEEN :start_date AND :end_date
                ORDER BY att.clock_in_date;
            """


class ReportService:

    def __init__(self):
        self.db = next(get_db())
        self.generators = {
            ReportTypes.VISITS: VisitReportGenerator(),
            ReportTypes.ATTENDANCE: AttendanceReportGenerator()
        }
    
    async def generate_report(self, request: ReportRequest) -> dict:

        end_date = request.end_date or datetime.nom()
        start_date = request.start_date or (end_date - timedelta(days=30))

        generator = self.generators[request.report_type]

        data  = await generator.generate(
            request.filter_by,
            request.filter_id,
            start_date,
            end_date
        )

        filter_details = await self._get_filter_details(
            request.filter_by,
            request.filter_id
        )

        summary = self._generate_summary(request.report_type, filter_details)

        pdf_bytes = self.generate_pdf(data, request.report_type, summary)


        return data, pdf_bytes

    async def _get_filter_details(self, filter_by: CategoryType, filter_id: uuid.UUID):
        tables = {
            CategoryType.EMPLOYEE: "employees",
            CategoryType.SERVICE: "services",
            CategoryType.DEPARTMENT: "departments"
        }

        with self.db as db:
            record = db.execute(
                f"SELECT * FROM {tables[filter_by]} WHERE id= :filter_id",
                {'filter_id': filter_id}
            ).mappings().all() 

        return record
    
    def _calculate_peak_visiting_hour(self, records):
        hours = []
        for record in records:
            check_in = record.get("check_in_at")
            if check_in:
                try:
                    # If check_in is a datetime.time object:
                    hour = check_in.hour
                except AttributeError:
                    # Otherwise, assume it's a string in "HH:MM:SS" format:
                    hour = int(check_in.split(":")[0])
                hours.append(hour)
        
        if not hours:
            return None  # No check-ins found.
        
        # Count frequency of each hour.
        hour_counts = Counter(hours)
        # most_common(1) returns a list with one tuple: (hour, frequency)
        peak_hour, _ = hour_counts.most_common(1)[0]
        return peak_hour

    def _calculate_highest_visiting_date(self, records):
        """
        Calculate and return the date with the highest number of visits from visit records.
        
        Args:
            records (list of dict): Each dict represents a visit record with a "date" key.
        
        Returns:
            date or None: The date (as a datetime.date object) with the most visits, or None if no dates exist.
        """
        dates = []
        for record in records:
            date_val = record.get("date")
            if date_val:
                if isinstance(date_val, str):
                    try:
                        # Parse the date assuming the format is YYYY-MM-DD
                        parsed_date = datetime.strptime(date_val, "%Y-%m-%d").date()
                        dates.append(parsed_date)
                    except ValueError:
                        # Fallback if parsing fails
                        dates.append(date_val)
                else:
                    dates.append(date_val)
        
        if not dates:
            return None
        
        # Count occurrences of each date
        date_counts = Counter(dates)
        # Get the date with the highest count
        highest_date, _ = date_counts.most_common(1)[0]
        return highest_date
    
    def _generate_summary(self, report_type: ReportTypes, data: List[Dict[str, Any]]) -> dict:

        if report_type == ReportTypes.VISIT:
            return{
                "total_visits" : len(data),
                "peack_visiting_hour" : self._calculate_peak_visiting_hour(data),
                "highest_visiting_dates" : self._calculate_highest_visiting_date(data),
                "avg_visits" : None
            }
        elif report_type ==  ReportTypes.ATTENDANCE:

            return{
                "average_arrival_time" : None,
                "average_time_at_work" : None,
                "average_arrival_time" : None,
                "average_arrival_time" : None,
            }

    def render_html_template(self, report_data, report_type: ReportTypes, summary):

        html_files = {
            ReportTypes.VISITS: "visits",
            ReportTypes.ATTENDANCE: "attendance"
        }
        template = env.get_template(f"{html_files[report_type]}.html")

        rendered_html = template.render(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            table_data=report_data,
            highest_day = {},
            peak_hour = {},
            top_employee = {},
            summary = summary
            # company_name = company_name
        )

        return rendered_html

    def generate_pdf(self, report_data, report_type: ReportTypes, summary):

        html_content = self.render_html_template(report_data, report_type, summary)
        pdf_bytes = HTML(string=html_content).write_pdf()

        return pdf_bytes


class ChromaConnectionSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ChromaConnectionSingleton, cls).__new__(cls, *args, **kwargs)
            cls._instance.client = Client()

        return cls._instance


class ChromaCollectionSingleton:
    _collections = {}

    @classmethod
    def get_collection(cls, collection_name: str):
        if collection_name not in cls._collections:
            client = ChromaConnectionSingleton().client
            cls._collections[collection_name] = client.get_or_create_collection(name=collection_name)
        return cls._collections





# ChromaService class with methods for creating collections, inserting embeddings, and querying
class ChromaService:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self.collection = ChromaCollectionSingleton.get_collection(collection_name)

    def create_collection(self, collection_name: str):
        # Optionally create and store another collection via the singleton
        return ChromaCollectionSingleton.get_collection(collection_name)

    def insert(self, embedding, metadata: dict, doc: str = "", vector_id: str = None):
        """
        Inserts an embedding with metadata into the collection.

        Args:
            embedding (list[float]): The embedding vector (e.g., 1024-dimensional for facial recognition).
            metadata (dict): Metadata to store (e.g., firstname, lastname, phone_number, date).
            doc (str): Optional document or description.
            vector_id (str): Optional unique identifier for the vector; autogenerated if not provided.
        """
        vector_id = vector_id or str(uuid.uuid4())
        self.collection.add(
            documents=[doc],
            embeddings=[embedding],
            metadatas=[metadata],
            ids=[vector_id]
        )

    def retrieve(self, embedding, top_k=1, filter_dict=None):
        """
        Queries the collection for similar embeddings.

        Args:
            embedding (list[float]): The query embedding vector.
            top_k (int): Number of top results to return.
            filter_dict (dict): Optional filter for metadata, e.g., {"date": {"$eq": "November 20, 2024"}}

        Returns:
            dict: Query results including ids, metadata, distances, etc.
        """
        query_params = {
            "query_embeddings": [embedding],
            "n_results": top_k,
            "include": ["metadata", "ids", "distances"]
        }
        if filter_dict:
            query_params["where"] = filter_dict
        results = self.collection.query(**query_params)
        return results

    def get_most_similar(self):

        pass
# Example usage:
if __name__ == '__main__':
    # Instantiate the service for the "faces" collection
    service = ChromaService("faces")

    # Sample 1024-dimensional embedding (dummy values for illustration)
    sample_embedding = [0.01] * 1024
    sample_metadata = {
        "firstname": "John",
        "lastname": "Doe",
        "phone_number": "123456789",
        "date": "November 20, 2024"
    }

    # Insert an embedding
    service.insert(sample_embedding, sample_metadata, doc="Face embedding for John Doe")

    # Query using the same sample embedding; for example, filter by today's date
    # (Format your date filter as stored in metadata)
    query_filter = {"date": {"$eq": "November 20, 2024"}}
    query_results = service.query(sample_embedding, top_k=1, filter_dict=query_filter)

    print("Query Results:", query_results)
