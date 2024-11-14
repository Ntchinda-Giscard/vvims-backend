from typing import Any, Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from sqlalchemy import func
from src import logger
from src.models import Employee, EmployeeRole, Role, Position, Attendance, Leave, Task, TaskStatusEnum, TaskStatus, Visit
from src.schema.output_type import EmployeeType, AttendnacePercentage, EmployeeOnLeave, TaskCompletionPercentage, \
    VisitsCountByDay
from src.schema.input_type import CreateEmployeeInput, CreateEmployeeRole, UpdateEmployeeInput, UpdatePasswordInputType, \
    EmployeeId
from datetime import timedelta, datetime
import math
from typing import List

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


def total_employee_on_leave(db: Session) -> EmployeeOnLeave:
    """
    Groups the attendance records by month, day, week of the year, and calculates the number of on-time, late, and abscent employees.
    :param db: A database session instance used to interact with the database.
    :return: A list of dictionaries, each containing the month, day, week of the year, number of on-time, late, and abscent employees.
    """
    
    leave_count = db.query(Employee).join(Leave, Employee.id == Leave.employee_id).filter(Leave.status =="ACCEPTED").count()

    return EmployeeOnLeave(total= leave_count)


def get_task_completion_percentage(db: Session, id) -> TaskCompletionPercentage:
    percentage = 0
    total_task_assigned = (db.query(Employee).join(Task, Employee.id == Task.assigned_to).count())

    total_completed_task = (
        db.query(Employee)
        .filter(Employee.id == id)
        .join(Task, Task.assigned_to == Employee.id)
                                               .join(TaskStatus, Task.id == TaskStatus.task_id)
                                               .filter(TaskStatus.status == TaskStatusEnum.COMPLETED)
                                               .count()
                                               )
    if total_completed_task == 0:
        return TaskCompletionPercentage(percentage = 0)
    percentage = (total_completed_task / total_task_assigned) * 100
    return TaskCompletionPercentage(percentage = percentage)






def get_visits_group_by_week_day(db: Session) -> List[VisitsCountByDay]:
    """
    Counts the number of visits made by employees in each weekday group (Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday).
    :param db: A database session instance used to interact with the database.
    :return: A list of dictionaries, each containing the weekday group name and the number of visits made by employees in that group.
    """
    
    today = datetime.now()

    # Calculate the start of the week (Monday) and end of the week (Sunday)
    start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
    end_of_week = start_of_week + timedelta(days=6)          # Sunday of this week

    # Step 1: Query the visitor data and group by day, ignoring the time part
    visitor_data = (
        session.query(
            func.date(Visit.date).label("visit_day"),  # Stripping the time part
            func.count(Visit.id).label("visitor_count")
        )
        .filter(
            func.date(Visit.date) >= start_of_week.date(),  # Ensure both sides are date-only
            func.date(Visit.date) <= end_of_week.date()
        )
        .group_by(func.date(Visit.date))
        .all()
    )

    # Step 2: Convert query results to a dictionary with date as key
    visitor_counts_by_day = {
        day.visit_day: day.visitor_count for day in visitor_data
    }

    # Step 3: Generate the full week with default visitor count of 0 for missing days
    full_week = [
        VisitorCountByDay(
            visit_day=start_of_week + timedelta(days=i),
            visitor_count=visitor_counts_by_day.get(start_of_week + timedelta(days=i), 0)
        )
        for i in range(7)  # 7 days in a week
    ]

    return full_week