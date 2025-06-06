import base64
from datetime import datetime
import strawberry
import uuid
from typing import Optional, List, ByteString, AnyStr, Any
from datetime import date


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
class EmployeeAttendatceType:
    id: uuid.UUID
    firstname: str
    lastname: str

@strawberry.type
class AttendanceType:
    # id: uuid.UUID
    employee: EmployeeAttendatceType
    clock_in: datetime
    clock_out: Optional[datetime]
    time_in_building: Optional[str]

@strawberry.type
class DayAttendanceType:
    date: datetime
    attendance: List[AttendanceType]

@strawberry.type
class DataType:
    data: List[DayAttendanceType]


@strawberry.type
class AttendnacePercentage:
    total_employee: int
    attendance_percentage: float


@strawberry.type
class EmployeeOnLeave:
    total: int

@strawberry.type
class TaskCompletionPercentage:
    percentage: float


@strawberry.type
class VisitsCountByDay:
    visit_day: str
    visitor_count: int


@strawberry.type
class VehicleCountByDay:
    visit_day: str
    visitor_count: int


@strawberry.type
class AttendanceCountByWeek:
    day: str
    late_employees: int
    on_time_employees: int
    present_employees: int


@strawberry.type
class CreateConvOutput:
    id: uuid.UUID

@strawberry.type
class AcceptParcipateEvent:
    id: uuid.UUID

@strawberry.type
class DenyParcipateEvent:
    id: uuid.UUID

@strawberry.type
class InsertMesaageOuput:
    id: uuid.UUID


@strawberry.type
class ParticipantType:
    firstname: str
    lastname: str

@strawberry.type
class EventType:
    title: str
    start_time:  str
    end_time: str
    description: str
    date: str


@strawberry.type
class EventWithUserParticipant:
    event: EventType
    participant: List[ParticipantType]


@strawberry.type
class MessageStatusOutput:
    state: str

@strawberry.type
class AppointmentTodayPercentage:
    today_count: int
    tomorrow_count: int
    percent: Optional[float] = None


@strawberry.type
class ReportsType:
    link:  str


@strawberry.type
class GenerateReportPayload:
    report_link: str
    filename: str


@strawberry.type
class VisitReportRow:
    visitor_name: str
    date: str
    check_in: Optional[str]
    check_out: Optional[str]
    reason: Optional[str]
    status: Optional[str]


@strawberry.type
class AttendanceReportRow:
    employee: str
    date: str
    status: str
    arrival: Optional[str]
    departure: Optional[str]
    late: Optional[bool]
    reason: Optional[str]


@strawberry.type
class ReportResult:
    type: str  # "visits" or "attendance"
    visit_data: Optional[List[VisitReportRow]] = None
    attendance_data: Optional[List[AttendanceReportRow]] = None