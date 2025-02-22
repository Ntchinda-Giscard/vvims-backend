from typing import Optional, List
from pydantic import  BaseModel
import strawberry
import uuid
from enum import Enum
from datetime import datetime
from datetime import date
from enum import Enum as PyEnum


@strawberry.enum
class CreateEmployeeRole(Enum):
    ADMIN = 'ADMIN'
    EMPLOYEE = 'EMPLOYEE'
    GUARD = 'GUARD'

@strawberry.input
class CreateEmployeeInput:
    firstname: str
    lastname: str
    password: str
    phone_number: str
    email: Optional[str]
    supervisor_id: Optional[uuid.UUID] = None
    company_id: uuid.UUID
    agency_id: Optional[uuid.UUID] = None
    position_id: uuid.UUID
    department_id: uuid.UUID
    service_id: uuid.UUID
    function: str
    region: str
    license: str
    address: str
    roles:  CreateEmployeeRole

@strawberry.input
class UpdateEmployeeInput:
    id: uuid.UUID
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None

@strawberry.input
class UpdatePasswordInputType:
    phone_number: str
    current_password: str
    new_password: str

class LoginInput(BaseModel):
    # firebase_token: Optional[str] = None
    phone_number: str
    password: str

class CreateEmployee(BaseModel):
    firstname: str
    lastname: str
    password: str
    phone_number: str
    email: Optional[str]
    supervisor_id: Optional[uuid.UUID] = None
    company_id: uuid.UUID
    agency_id: Optional[uuid.UUID] = None
    position_id: uuid.UUID
    department_id: uuid.UUID
    service_id: uuid.UUID
    function: str
    roles:  CreateEmployeeRole

class CreatVisitWithVisitor(BaseModel):
    firstname: Optional[str]
    lastname: Optional[str]
    phone_number: Optional[str]
    id_number: Optional[str]
    host_employee: Optional[uuid.UUID]
    host_department: Optional[uuid.UUID]
    host_service: Optional[uuid.UUID]
    vehicle: Optional[uuid.UUID]
    visitor: Optional[uuid.UUID]
    status: str = 'PENDING'
    reason: str
    reg_no: Optional[str]

@strawberry.input
class CrateVisitWithVisitorType:
    firstname: str
    lastname: Optional[str]
    phone_number: str
    id_number: str
    company_id: uuid.UUID
    host_employee: Optional[uuid.UUID]
    host_department: Optional[uuid.UUID]
    host_service: Optional[uuid.UUID]
    vehicle: Optional[uuid.UUID]
    visitor: Optional[uuid.UUID]
    status: str = 'PENDING'
    reason: str
    reg_no: str

@strawberry.enum
class VisitStatus(Enum):
    ACCEPTED = 'ACCEPTED'
    REJECTED = 'REJECTED'
    PENDING = 'PENDING'

@strawberry.input
class AddVisitorBrowserInputType:
    host_employee: Optional[uuid.UUID] = None
    host_department: Optional[uuid.UUID] = None
    host_service: Optional[uuid.UUID] = None
    visitor: Optional[uuid.UUID] = None
    vehicle: Optional[uuid.UUID] = None
    status: str
    reason: Optional[str]
    reg_no: Optional[str] = None
    firstname: str
    lastname: str
    id_number: str
    company_id: uuid.UUID
    phone_number: str


@strawberry.input
class AttendanceInpuType:
    start_date: datetime
    end_date: datetime


@strawberry.input
class DateRangeInputType:
    from_date: datetime
    to_date: datetime

@strawberry.input
class EmployeeId:
    id: uuid.UUID


@strawberry.input
class CreateConvInput:
    is_group: bool
    name: Optional[str] = None
    first_participant: uuid.UUID
    second_participants: uuid.UUID

@strawberry.input
class ParticipantInput:
    id: uuid.UUID


@strawberry.input
class MessageInput:
    conversation_id: uuid.UUID
    content: str
    employee_id: uuid.UUID


@strawberry.input
class EventByUserInput:
    date: date
    employee_id: uuid.UUID

@strawberry.input
class MessageStatusInput:
    id: List[uuid.UUID]
    status: str

@strawberry.input
class EmployeeAppointmentId:
    id: uuid.UUID



class ReportTypes(PyEnum):
    ATTENDANCE = 'attendance'
    VISITS = 'visits'
    TASKS = 'tasks'

class CategoryType(PyEnum):
    EMPLOYEE = "employee"
    SERVICE = "service"
    DEPARTMENT = "department"


class ReportRequest(BaseModel):
    report_type: ReportType
    filter_by: CategoryType
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None