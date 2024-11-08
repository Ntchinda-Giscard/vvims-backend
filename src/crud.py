from typing import Any, Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from sqlalchemy import func
from src import logger
from src.models import Employee, EmployeeRole, Role, Position, Attendance, Leave
from src.schema.output_type import EmployeeType, AttendnacePercentage
from datetime import timedelta, datetime
import math

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_attendance_for_day(db: Session, date):

    return db.query(Attendance).join(Employee).filter(
        and_(
            Attendance.clock_in_time >= date,
            Attendance.clock_out_time <= date + timedelta(days=1) # Assuming 24-hour time
        )
    )

def get_employee_by_phone(db: Session, phone_number: str) -> EmployeeType :
    """
    Gets an employee based on his phone number
    :param db:
    :param phone_number:
    :return:
    """
    employee_with_role: Optional[EmployeeType] =  (db.query(Employee)
        .join(EmployeeRole, Employee.id == EmployeeRole.employee_id)
        .join(Role, EmployeeRole.role_id == Role.id)
        .join(Position, Employee.position_id == Position.id)
        .filter(Employee.phone_number == phone_number)
        .options(
            joinedload(Employee.roles).joinedload(EmployeeRole.role),
            joinedload(Employee.position)
        )
        .first()
    )
    # employee = db.query(Employee).first()
    if not employee_with_role:
        raise Exception("Employee not found or wrong credentials")
    return employee_with_role

def authenticate_employee(db: Session, phone_number: str, password: str):
    """
    :param db: A database session instance used to interact with the database.
    :param phone_number: The phone number of the employee attempting to authenticate.
    :param password: The password provided by the employee for authentication.
    :return: The authenticated employee object if authentication is successful, or False if authentication fails.
    """
    employee = get_employee_by_phone(db, phone_number)
    if employee:
        print("Employee====>")
    if pwd_context.verify(password, employee.password):
        print("Same password")


    if not employee or not pwd_context.verify(password, employee.password):
        return False
    return  employee



def count_attendance_percentage(db: Session) -> AttendnacePercentage:
    """
    Counts the total number of employees, and calculates the percentage of employees
    who have logged in within the last 24 hours.
    
    :param db: A database session instance used to interact with the database.
    :return: An instance of AttendanceStats containing the total number of employees and attendance percentage.
    """
    total_employees = db.query(Employee).count()
    
    if total_employees == 0:
        return AttendanceStats(total_employees=0, attendance_percentage=0.0)

    last_24_hours = datetime.now() - timedelta(hours=24)
    attendance_count = db.query(Attendance).filter(Attendance.clock_in_time >= last_24_hours).count()

    attendance_percentage = (attendance_count / total_employees) * 100
    return AttendnacePercentage(
        total_employee =total_employees,
        attendance_percentage = math.ceil(attendance_percentage)
    )

    # {
    #     "total_employees": total_employees,
    #     "attendance_percentage": (attendance_count / total_employees) * 100 if total_employees else 0
    # }


def on_leave_number(db: Session):
    """
    Groups the attendance records by month, day, week of the year, and calculates the number of on-time, late, and abscent employees.
    :param db: A database session instance used to interact with the database.
    :return: A list of dictionaries, each containing the month, day, week of the year, number of on-time, late, and abscent employees.
    """
    
    leave_count = db.query(Employee).join(Leave, Employee.id == Leave.employee_id).filter(Leave.status="ACCEPTED").count()
    print("LEave count", leave_count)


    return leave_count