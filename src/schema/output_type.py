import base64
from datetime import datetime
import strawberry
import uuid
from typing import Optional, List, ByteString, AnyStr, Any


@strawberry.type
class RoleType:
    id: uuid.UUID
    role_name: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

@strawberry.type
class EmployeeCreationType:
    id: uuid.UUID
    firstname: str
    lastname: str
    phone_number: str

@strawberry.type
class EmployeeUpdateType:
    id: Optional[uuid.UUID]
    firstname: Optional[str]
    lastname: Optional[str]
    address: Optional[str]
    phone_number: Optional[str]

@strawberry.type
class UpdatePasswordOutputType:
    success: str

@strawberry.type
class CreateVisitorType:
    id: uuid.UUID

@strawberry.type
class EmployeeRole:
    id: Optional[uuid.UUID]
    employee_id: Optional[uuid.UUID]
    role_id: Optional[uuid.UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    role: RoleType

@strawberry.type
class PositionType:
    id: uuid.UUID
    level: int

@strawberry.type
class EmployeeType:
    id: uuid.UUID
    company_id: Optional[uuid.UUID]
    agency_id:  Optional[uuid.UUID]
    firstname: Optional[str]
    lastname: Optional[str]
    phone_number: Optional[str]
    email: Optional[str]
    password: Optional[str]
    service_id: Optional[uuid.UUID]
    department_id: Optional[uuid.UUID]
    position_id: Optional[uuid.UUID]
    supervisor_id: Optional[uuid.UUID]
    function: Optional[str]
    profile_picture: Optional[uuid.UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    roles: Optional[List[EmployeeRole]]
    position: Optional[PositionType]



@strawberry.type
class LoginReturnType:
    token: str
    employee: EmployeeType

@strawberry.type
class CreateVisitorReturnType:
    id: uuid.UUID


@strawberry.type
class EmployeeType:
    id: uuid.UUID
    firstname: str
    lastname: str

@strawberry.type
class AttendanceType:
    id: uuid.UUID
    employee: EmployeeType
    clock_in: datetime
    clock_out: Optional[datetime]
    time_in_building: Optional[str]

@strawberry.type
class DayAttendanceType:
    date: datetime
    attendance: List[AttendanceType]