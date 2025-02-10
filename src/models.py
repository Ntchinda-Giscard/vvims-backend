from datetime import timezone
from dataclasses import dataclass
from sqlalchemy import BigInteger, Column, Integer, String, ForeignKey, Enum, func, DateTime, UUID, Float, Enum, Date, Time, \
    Interval, ARRAY, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from src.database import Base
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import UUID
import uuid
from enum import Enum as PyEnum



class Role(Base):
    __tablename__ = 'roles'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    role_name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EmployeeRole(Base):
    __tablename__ = 'employee_roles'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey('roles.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    employee = relationship('Employee', back_populates='roles')  # Singular 'employee'
    role = relationship('Role')


class Company(Base):
    __tablename__ = 'companies'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(UUID(as_uuid=True), ForeignKey('text_content.id'))
    email = Column(String, nullable=False, unique=True)
    location = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    profile_picture = Column(String, nullable=True)
    address = Column(String)
    city = Column(String, nullable=False)
    region = Column(String, nullable=False)
    neighborhood = Column(String)
    po_box = Column(String, nullable=True)
    phone_number = Column(String, nullable=True, unique=True)
    abbrev = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # relationships
    agencies = relationship('Agency', back_populates='company')
    company_settings = relationship('CompanySettings', back_populates='company')
    visitors = relationship('Visitor', back_populates='company')


class Agency(Base):
    __tablename__ = 'agencies'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False, unique=True)
    name = Column(UUID(as_uuid=True), ForeignKey('text_content.id'))
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False)
    location = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    address = Column(String)
    city = Column(String, nullable=False)
    region = Column(String, nullable=False)
    office = Column(String, nullable=True)
    neighborhood = Column(String)
    po_box = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)

    company = relationship('Company', back_populates='agencies')
    departments = relationship('Department', back_populates='agency')


class Service(Base):
    __tablename__ = 'services'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(UUID(as_uuid=True), ForeignKey('text_content.id'))
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    chief_service = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=True)
    agency_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=True)

    # Relationships
    department = relationship('Department', back_populates='services')
    visit = relationship('Visit', back_populates='service')

    # Specify the foreign key to use in the employees relationship
    employees = relationship('Employee', back_populates='service', foreign_keys='Employee.service_id')


class Position(Base):
    __tablename__ = 'positions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(UUID(as_uuid=True), ForeignKey('text_content.id'))
    level = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'))

    employee = relationship('Employee', back_populates='position')

class Task(Base):
    __tablename__= 'tasks'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    assigned_by = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    due_date = Column(Date)

    #relationships
    event = relationship("Event", back_populates="tasks")
    assigned_to_user = relationship("Employee", foreign_keys=[assigned_to], back_populates="tasks_assigned_to")
    assigned_by_user = relationship("Employee", foreign_keys=[assigned_by], back_populates="tasks_assigned_by")

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    firstname = Column(String, nullable=False)
    lastname = Column(String, nullable=False)
    phone_number = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=True, unique=True)
    password = Column(String, nullable=False)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False)
    agency_id = Column(UUID(as_uuid=True), ForeignKey('agencies.id'), nullable=True)
    service_id = Column(UUID(as_uuid=True), ForeignKey('services.id'), nullable=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id'),
                           nullable=False)  # Foreign key for Department
    position_id = Column(UUID(as_uuid=True), ForeignKey('positions.id'), unique=False)
    supervisor_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    function = Column(String, nullable=False)
    profile_picture = Column(UUID(as_uuid=True), ForeignKey('files.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    firebase_token = Column(String, nullable=True)
    ####
    region = Column(String, nullable=True)
    id_card_number = Column(String, nullable=True)
    license = Column(String, nullable=True)
    address = Column(String, nullable=True)
    password_change_at = Column(DateTime(timezone=True))
    messages = relationship('Message', back_populates='employee')
    message_status = relationship('MessageStatus', back_populates='employee')
    typing_status = relationship('TypingStatus', back_populates='employee')
    employee_conv = relationship('EmployeeConversation', back_populates='employees')


    # Relationships
    roles = relationship('EmployeeRole', back_populates='employee')
    service = relationship('Service', back_populates='employees', foreign_keys='Employee.service_id')
    department = relationship('Department', back_populates='employees',foreign_keys='Employee.department_id')  # Define foreign key for Department
    leaves = relationship('Leave', back_populates='employee', cascade='all, delete-orphan')
    supervisor = relationship('Employee', remote_side=[id], backref='subordinates')
    position = relationship('Position', back_populates='employee')
    attendance = relationship('Attendance', back_populates='employee', cascade="all, delete-orphan")
    files = relationship('UploadedFile', back_populates='employee')
    employee_shifts = relationship("EmployeeShift", back_populates='employee')
    employee_notifications = relationship("EmployeeNotification", back_populates='employee')
    visit = relationship('Visit', back_populates='employee')
    appointments = relationship("Appointment", back_populates='employees')

    participants = relationship("EventParticipant", back_populates="employee")
    event = relationship("Event", back_populates="employee")
    task_status = relationship("TaskStatus", back_populates='employee')
    event_notifications = relationship("EventNotification", back_populates='employee')
    alarms = relationship("Alarm", back_populates="employee")
    tasks_assigned_to = relationship("Task", foreign_keys=[Task.assigned_to], back_populates="assigned_to_user")
    tasks_assigned_by = relationship("Task", foreign_keys=[Task.assigned_by], back_populates="assigned_by_user")
    group = relationship('Group', back_populates='employee')
    group_members = relationship('GroupMembers', back_populates='employee')
    # employee = relationship('Employee', back_populates='group_members')
    # employee = relationship('Employee', back_populates='group')



class Department(Base):
    __tablename__ = 'departments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(UUID(as_uuid=True), ForeignKey('text_content.id'))
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False)
    agency_id = Column(UUID(as_uuid=True), ForeignKey('agencies.id'), nullable=True)
    parent_department_id = Column(UUID(as_uuid=True), ForeignKey('departments.id'), nullable=True)
    chief_department = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    abrev_code= Column(String)
    status = Column(String)

    # Relationships
    agency = relationship('Agency', back_populates='departments')
    services = relationship('Service', back_populates='department')
    parent_department = relationship('Department', remote_side=[id])
    visit = relationship('Visit', back_populates='department')

    # Specify foreign_keys argument to resolve ambiguity
    employees = relationship('Employee', back_populates='department', foreign_keys='Employee.department_id')


class TextContent(Base):
    __tablename__ = 'text_content'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    content = Column(String, nullable=False)
    translations = Column(UUID(as_uuid=True), ForeignKey('translations.id'))


class Translations(Base):
    __tablename__ = 'translations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    language_iso_code = Column(String)
    content = Column(UUID(as_uuid=True), ForeignKey('text_content.id'))


class UploadedFile(Base):
    __tablename__ = 'files'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    file_name = Column(String, nullable=True)
    file_url = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    file_size = Column(Float, nullable=True)

    # Relationships
    employee = relationship('Employee', back_populates='files')
    # leaves = relationship('Leave', back_populates='files')


class Visitor(Base):
    __tablename__ = 'visitors'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    firstname = Column(String)
    lastname = Column(String)
    photo = Column(UUID(as_uuid=True), ForeignKey('files.id'), nullable=True)
    front_id = Column(UUID(as_uuid=True), ForeignKey('files.id'), nullable=True)
    back_id = Column(UUID(as_uuid=True), ForeignKey('files.id'), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'), nullable=True)
    id_number = Column(String, unique=True)
    phone_number = Column(String, nullable=True)

    # relationship
    visit = relationship('Visit', back_populates='visitors')
    company = relationship('Company', back_populates='visitors')
    appointments = relationship("Appointment", back_populates='visitors')


class Visit(Base):
    __tablename__ = 'visits'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    host_employee = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    host_department = Column(UUID(as_uuid=True), ForeignKey('departments.id'), nullable=True)
    host_service = Column(UUID(as_uuid=True), ForeignKey('services.id'), nullable=True)
    visitor = Column(UUID(as_uuid=True), ForeignKey('visitors.id'), nullable=False)

    vehicle = Column(UUID(as_uuid=True), ForeignKey('vehicles.id'), nullable=True)
    status = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    date = Column(Date, server_default=func.now())
    check_in_at = Column(Time)
    check_out_at = Column(Time)
    reg_no = Column(String, nullable=True)

    # relationship
    employee = relationship('Employee', back_populates='visit')
    department = relationship('Department', back_populates='visit')
    service = relationship('Service', back_populates='visit')
    visitors = relationship('Visitor', back_populates='visit')
    employee_notifications = relationship('EmployeeNotification', back_populates='visits')


class Vehicle(Base):
    __tablename__ = 'vehicles'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    license = Column(String, unique=True)
    make = Column(String, nullable=True)
    brand = Column(String, nullable=True)
    flagged = Column(Boolean, default=False)
    color = Column(String, nullable=True)

    # visit = relationship('Visit', back_populates = 'vehicle')


class LeaveApprovalStatus(Base):
    __tablename__='leave_approval_status'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    reason = Column(String)
    leave_id = Column(UUID(as_uuid=True), ForeignKey('leaves.id'))
    leave_status = Column(String)

    #relationships
    leaves = relationship('Leave', back_populates='leave_approval_status')

class Leave(Base):
    __tablename__ = 'leaves'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    types = Column(UUID(as_uuid=True), ForeignKey('leave_types.id'))
    # file = Column(UUID(as_uuid=True), ForeignKey('files.id'))
    file = Column(String)
    status = Column(String)
    leave_type = Column(String)
    other_description = Column(String)
    comment = Column(String)
    start_time = Column(Time)
    end_time = Column(Time)

    employee = relationship('Employee', back_populates='leaves')
    leave_approval_status = relationship('LeaveApprovalStatus', back_populates='leaves')
    approval = relationship('LeaveApproval', back_populates='leave', cascade='all, delete-orphan')
    leave_types = relationship("LeaveType", back_populates='leave')
    # files = relationship('UploadedFile', back_populates='leaves')


class LeaveType(Base):
    __tablename__= 'leave_types'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    types = Column(String)

    #relationships
    leave = relationship("Leave", back_populates='leave_types')

class LeaveApproval(Base):
    __tablename__ = 'leave_approval'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    leave_id = Column(UUID(as_uuid=True), ForeignKey('leaves.id'))
    approver_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'))
    approval_status = Column(String)
    comments = Column(String, nullable=True)

    leave = relationship("Leave", back_populates='approval')
    approver = relationship("Employee")


class Attendance(Base):
    __tablename__ = 'attendance'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), unique=True)
    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'), nullable=True)
    clock_in_time = Column(DateTime(timezone=True), nullable=True)
    clock_out_time = Column(DateTime(timezone=True), nullable=True)
    clock_in_date = Column(Date, server_default=func.now(), unique=False)
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=True)
    building_id = Column(UUID(as_uuid=True), nullable=True)


    # relationship
    employee = relationship('Employee', back_populates='attendance')
    shift = relationship('Shift', back_populates='attendance')
    attendance_state = relationship('AttendanceState', back_populates='attendance')

class AttendanceState(Base):
    __tablename__ = 'attendance_state'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    is_late = Column(Boolean, nullable=True)
    attendance_id = Column(UUID(as_uuid=True), ForeignKey('attendance.id'), unique=True)

    # relationship
    attendance = relationship('Attendance', back_populates='attendance_state')

class Shift(Base):
    __tablename__ = 'shifts'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    working_days = Column(ARRAY(Integer), nullable=True)

    employee_shifts = relationship('EmployeeShift', back_populates='shift')
    attendance = relationship('Attendance', back_populates='shift')


class CompanySettings(Base):
    __tablename__ = 'company_settings'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    start_work_time = Column(Time, nullable=False)
    end_work_time = Column(Time, nullable=False)
    max_late_time = Column(Interval, nullable=False)
    break_duration = Column(Interval, nullable=True)
    max_leave_days_per_year = Column(Integer, nullable=True)
    number_of_leave_days = Column(Integer, nullable=True)
    working_days = Column(ARRAY(Integer), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('companies.id'))
    # relationships
    company = relationship('Company', back_populates='company_settings')


class EmployeeShift(Base):
    __tablename__ = 'employee_shifts'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'))
    shift_id = Column(UUID(as_uuid=True), ForeignKey('shifts.id'))
    # relationship
    employee = relationship('Employee', back_populates='employee_shifts')
    shift = relationship('Shift', back_populates='employee_shifts')


class AppVersions(Base):
    __tablename__ = 'app_versions'
    version = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EmployeeNotificationType(PyEnum):
    EVENTS = 'events'
    MESSAGES = 'messages'
    VISITS  = 'visits'

class EmployeeNotification(Base):
    __tablename__ = 'employee_notifications'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    action = Column(String, nullable=False)
    type = Column(Enum(EmployeeNotificationType))
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False)
    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=True)
    visits_id = Column(UUID(as_uuid=True), ForeignKey('visits.id'), nullable=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    employee = relationship("Employee", back_populates='employee_notifications')
    event = relationship('Event', back_populates='employee_notifications')
    visits = relationship('Visit', back_populates='employee_notifications')
    messages = relationship('Message', back_populates='employee_notifications')


class Appointment(Base):
    __tablename__ = "appointments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    visitor_id = Column(UUID(as_uuid=True), ForeignKey('visitors.id'), nullable=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    start_time = Column(Time)
    end_time = Column(Time, nullable=True)
    description = Column(String)
    date = Column(Date)
    status=Column(String)

    employees = relationship("Employee", back_populates='appointments')
    visitors = relationship("Visitor", back_populates='appointments')


class Location(Base):
    __tablename__ = "locations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    location = Column(Geometry(geometry_type="POLYGON", srid=4326), nullable=True)
    buidling_id = Column(UUID(as_uuid=True), nullable=True)


class Event(Base):
    __tablename__="events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    title= Column(String(255), nullable=False)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    orgenizer_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)

    #relationships
    employee = relationship("Employee", back_populates="event")
    participants = relationship("EventParticipant", back_populates="event")
    tasks = relationship("Task", back_populates="event")
    employee_notifications = relationship('EmployeeNotification', back_populates='event')

class ParticipantStatus(PyEnum):
    PENDING = "PENDING"
    COMPLETED = "ACCEPTED"
    ON_GOING = "DECLINED"

class EventParticipant(Base):
    __tablename__ = 'event_participants'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    status = Column(Enum(ParticipantStatus), default=ParticipantStatus.PENDING)

    #RELATIONSHIPS

    event = relationship("Event", back_populates="participants")
    employee = relationship("Employee", back_populates="participants")



class TaskStatusEnum(PyEnum):
    PENDING = "PENDIING"
    ONGOING = "ONGOING"
    REVIEWING = "REVIEWING"
    COMPLETED = "COMPLETED"


class TaskStatus(Base):
    __tablename__ = 'task_status'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.PENDING)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id'), nullable=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    comment = Column(Text)

    #relationships
    tasks = relationship("Task")
    employee = relationship("Employee", back_populates='task_status')


class EventNotification(Base):
    __tablename__ = 'event_notification'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    message = Column(Text)
    read = Column(Boolean, default=False)

    #relationship
    employee = relationship("Employee", back_populates='event_notifications')
    event = relationship("Event")


class Alarm(Base):
    __tablename__ = 'alarms'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    event_id = Column(UUID(as_uuid=True), ForeignKey('events.id'), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    alarm_time = Column(DateTime)

    employee = relationship("Employee", back_populates="alarms")
    event = relationship("Event")


class Conversation(Base):
    __tablename__= 'conversations'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String)
    is_group = Column(Boolean, default=False)

    #relationship
    messages = relationship('Message', back_populates='conversation')
    employee_conv = relationship('EmployeeConversation', back_populates='conversation')

class EmployeeConversation(Base):
    __tablename__ = 'employee_conversation'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)

    #relationship
    employees = relationship('Employee', back_populates='employee_conv')
    conversation = relationship('Conversation', back_populates='employee_conv')

class Message(Base):
    __tablename__ = 'messages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    sender_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey('conversations.id'), nullable=False)
    content = Column(Text, nullable=True)
    is_read = Column(Boolean, default=False)
    message_mobile_id = Column(String(50))
    #relations
    employee = relationship('Employee', back_populates='messages')
    conversation = relationship('Conversation', back_populates='messages')
    attachment = relationship('Attachment', back_populates='message')
    message_status = relationship('MessageStatus', back_populates='message')
    employee_notifications = relationship('EmployeeNotification', back_populates='messages')



class MessageStatuses(PyEnum):
    SENT = "sent"
    DELIVERED = "delivered"
    SEEN = "seen"

class MessageStatus(Base):
    __tablename__ = 'message_statuses'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    status = Column(Enum(MessageStatuses), default=MessageStatuses.SENT)
    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id'), nullable=False)

    employee = relationship('Employee', back_populates='message_status')
    message = relationship('Message', back_populates='message_status')

class FileTypeEnum(PyEnum):
    image= 'image'
    pdf = 'pdf'
    audio = 'audio'
    video = 'video'
    other = 'other'

class Attachment(Base):
    __tablename__ = 'attachments'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    message_id = Column(UUID(as_uuid=True), ForeignKey('messages.id'), nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    extension = Column(String(5), nullable=True)
    file_size = Column(String, nullable=True)
    mime_type = Column(String(50))
    height = Column(String, nullable=True)
    width = Column(String, nullable=True)
    length = Column(String, nullable=True)
    filename= Column(String(50), nullable=False)


    #relationship
    message = relationship('Message', back_populates='attachment')


class TypingStatus(Base):
    __tablename__ = 'typing_statuses'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    is_typing = Column(Boolean, default=False)

    employee = relationship('Employee', back_populates='typing_status')

class Group(Base):
    __tablename__ = 'groups'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    name = Column(String(50), nullable=False)
    creator_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    group_description = Column(String(255), nullable=True)

    # Relationships
    employee = relationship('Employee', back_populates='group')
    group_members = relationship('GroupMembers', back_populates='group')
    group_messages = relationship('GroupMessages', back_populates='group')  # FIXED

class GroupMembers(Base):
    __tablename__ = 'group_members'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'), nullable=False)
    member_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    is_admin = Column(Boolean, default=False)

    # Relationships
    employee = relationship('Employee', back_populates='group_members')
    group = relationship('Group', back_populates='group_members')

class GroupMessages(Base):
    __tablename__ = 'group_messages'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    group_id = Column(UUID(as_uuid=True), ForeignKey('groups.id'), nullable=False)
    content = Column(String, nullable=True)
    attachment = Column(UUID(as_uuid=True), ForeignKey('attachments.id'), nullable=False)

    # Relationships
    group = relationship('Group', back_populates='group_messages')

class ReportTypes(PyEnum):
    ATTENDANCE = 'attendance'
    VISITS = 'visits'
    TASKS = 'tasks'

class Report(Base):

    __tablename__ = "reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    report_link = Column(String, nullable=False)
    from_date = Column(Date, nullable=False)
    to_date = Column(Date, nullable=False)
    types = Column(Enum(ReportTypes), default=ReportTypes.VISITS)