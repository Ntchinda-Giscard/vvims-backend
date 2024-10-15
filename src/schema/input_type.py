from typing import Optional
from pydantic import  BaseModel
import strawberry
import uuid
from enum import Enum

@strawberry.enum
class CreateEmployeeRole(Enum):
    ADMIN = 'ADMIN'
    EMPLOYEE = 'EMPLOYEE'

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
    # password: str
    phone_number: Optional[str] = None
    # email: Optional[str]
    # supervisor_id: Optional[uuid.UUID] = None
    # company_id: uuid.UUID
    # agency_id: Optional[uuid.UUID] = None
    # position_id: uuid.UUID
    # department_id: uuid.UUID
    # service_id: uuid.UUID
    # function: str
    # region: str
    # license: str
    address: Optional[str] = None
    # roles:  CreateEmployeeRole

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