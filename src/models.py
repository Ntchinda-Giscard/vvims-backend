from sqlalchemy import Column, Integer, String, ForeignKey, Enum, func, DateTime, UUID, Float, Enum, Date, Time, \
    Interval, ARRAY, Boolean
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    # realtionships
    agencies = relationship('Agency', back_populates='company')
    company_settings = relationship('CompanySettings', back_populates='company')


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

    # Relationships
    department = relationship('Department', back_populates='services')

    # Specify the foreign key to use in the employees relationship
    employees = relationship('Employee', back_populates='service', foreign_keys='Employee.service_id')


class Position(Base):
    __tablename__ = 'positions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(UUID(as_uuid=True), ForeignKey('text_content.id'))
    level = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    employee = relationship('Employee', back_populates='position')


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
    ####
    region = Column(String, nullable=True)
    id_card_number = Column(String, nullable=True)
    license = Column(String, nullable=True)
    address = Column(String, nullable=True)

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
    # shifts = relationship('Shift', secondary='employee_shifts', primaryjoin='Employee.id == EmployeeShift.employee_id', secondaryjoin='Shift.id == EmployeeShift.shift_id', back_populates='employees')


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

    # Relationships
    agency = relationship('Agency', back_populates='departments')
    services = relationship('Service', back_populates='department')
    parent_department = relationship('Department', remote_side=[id])

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

    employee = relationship('Employee', back_populates='files')


class Visitor(Base):
    __tablename__ = 'visitors'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    firstname = Column(String)
    lastname = Column(String)
    photo = Column(UUID(as_uuid=True), ForeignKey('files.id'), nullable=True)
    id_number = Column(String, unique=True)


class Visit(Base):
    __tablename__ = 'visits'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    host_employee = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    host_department = Column(UUID(as_uuid=True), ForeignKey('departments.id'), nullable=True)
    host_service = Column(UUID(as_uuid=True), ForeignKey('services.id'), nullable=True)
    vehicle = Column(UUID(as_uuid=True), ForeignKey('vehicles.id'), nullable=True)
    visitor = Column(UUID(as_uuid=True), ForeignKey('visitors.id'), nullable=False)


class Vehicle(Base):
    __tablename__ = 'vehicles'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    license = Column(String, unique=True)
    make = Column(String, nullable=True)
    color = Column(String, nullable=True)


class LeaveStatus(PyEnum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'


class LeaveType(PyEnum):
    SICK = "SICK"
    VACATION = "VACATION"
    PERSONAL = "PERSONAL"


class Leave(Base):
    __tablename__ = 'leaves'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    leave_type = Column(Enum(LeaveType), nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    comment = Column(String)

    employee = relationship('Employee', back_populates='leaves')
    approval = relationship('LeaveApproval', back_populates='leave', cascade='all, delete-orphan')


class LeaveApproval(Base):
    __tablename__ = 'leave_approval'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    leave_id = Column(UUID(as_uuid=True), ForeignKey('leaves.id'))
    approver_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'))
    approval_status = Column(Enum(LeaveStatus), nullable=False)
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
    clock_in_date = Column(Date, server_default=func.now(), unique=True)


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