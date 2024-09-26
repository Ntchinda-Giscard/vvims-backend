from typing import Any, Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload
from src import logger
from src.models import Employee, EmployeeRole, Role, Position
from src.schema.output_type import EmployeeType

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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