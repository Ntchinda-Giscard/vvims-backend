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