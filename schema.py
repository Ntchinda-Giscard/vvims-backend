import base64
import typing
import strawberry
from fastapi import Depends
from sqlalchemy.sql.coercions import expect
from strawberry.types import Info
from src.auth import create_token, get_current_user, oauth2_scheme
from src.crud import pwd_context, authenticate_employee
from src.database import get_db
from src.models import Employee, Role, EmployeeRole
from src.schema.input_type import CreateEmployeeInput, CreateEmployeeRole, UpdateEmployeeInput, UpdatePasswordInputType
from src import logger
from src.schema.output_type import EmployeeCreationType, EmployeeType, LoginReturnType, EmployeeUpdateType, \
    UpdatePasswordOutputType


# Custom context to hold the user info
class Context:
    def __init__(self, token: typing.Optional[str]):
        self.token = token
        self.user = None

    def set_user(self, user_id: str):
        self.user = user_id

async def get_context(token: typing.Optional[str] = Depends(oauth2_scheme)) -> Context:
    context = Context(token=token)
    if token:
        user_id = get_current_user(token)
        context.set_user(user_id)
    return context

@strawberry.type
class Query:
    @strawberry.field
    def name(self) -> str:
        return "Strawberry"

    @strawberry.field
    def login_employee(self, phone_number: str, password: str, firebase_token: typing.Optional[str] = None) -> typing.Optional[LoginReturnType]:
        with next(get_db()) as db:
            employee_with_role = authenticate_employee(db, phone_number, password)
            employee_with_role.firebase_token = firebase_token if firebase_token else employee_with_role.firebase_token
            if employee_with_role:
                token = create_token(employee_with_role)
                # token = base64.b64encode(token).decode('utf-8')
                return LoginReturnType(
                    token = f"{token}",
                    employee = employee_with_role
                )
            else:
                raise Exception("Employee not found or wrong credentials")



@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_employee(self, employee: CreateEmployeeInput) -> EmployeeCreationType:
        """
        Function that adds an employee to the database to a specific
        department, services, company, agency if provided, and roles in the company.
        :param employee:
        :return EmployeeCreationType:
        """
        with next(get_db()) as db:
            hashed_pwd = pwd_context.hash(employee.password)
            print("Plain password:", employee.password)
            print("Hashed password:", hashed_pwd)
            db_employee = Employee(
                firstname=employee.firstname,
                lastname=employee.lastname,
                company_id=employee.company_id,
                agency_id = employee.agency_id,
                email=employee.email,
                password=hashed_pwd,
                function=employee.function,
                position_id=employee.position_id,
                service_id=employee.service_id,
                department_id=employee.department_id,
                supervisor_id=employee.supervisor_id,
                phone_number=employee.phone_number,
                region=employee.region,
                license=employee.license,
                address=employee.address
            )
            try:
                db.add(db_employee)
                db.commit()

                employee_role = db.query(Role).filter_by(role_name="EMPLOYEE").one()
                print("Role employee found",employee_role)
                employee_role_1 = EmployeeRole(employee_id=db_employee.id, role_id=employee_role.id)
                print("Employee roles",employee_role_1)
                if employee.roles == CreateEmployeeRole.ADMIN:
                    print("User chose admin role:", employee.roles)
                    admin_role = db.query(Role).filter_by(role_name="ADMIN").one()
                    print("Admin role found", admin_role)
                    employee_role_2 = EmployeeRole(employee_id=db_employee.id, role_id=admin_role.id)
                    print("Employee admin role",employee_role_2)
                    db.add_all([employee_role_1, employee_role_2])
                    db.commit()
                    print("Employee added role for admin and employee")
                else:
                    db.add(employee_role_1)
                    db.commit()
                    print("Employee added roles for employee only")
                    db.refresh(db_employee)

                return EmployeeCreationType(
                    id=db_employee.id,
                    firstname=db_employee.firstname,
                    lastname=db_employee.lastname,
                    phone_number=db_employee.phone_number
                )
            except Exception as e:
                logger.exception(e)
                db.rollback()
                db.close()
                raise e
            finally:
                db.close()

    @strawberry.mutation
    def update_user_info(self, employee: UpdateEmployeeInput) -> EmployeeUpdateType:
        """
        Function that adds an employee to the database to a specific
        :param employee:
        :return EmployeeCreationType:
        """

        with next(get_db()) as db:
            try:
                user = db.query(Employee).filter(Employee.id == employee.id).one()
                user.firstname = employee.firstname if employee.firstname else user.firstname
                user.lastname = employee.lastname if employee.lastname else user.lastname
                user.address = employee.address if employee.address else user.address
                user.phone_number = employee.phone_number if employee.phone_number else user.phone_number

                db.commit()
                return EmployeeUpdateType(
                    id=employee.id,
                    firstname=employee.firstname,
                    lastname=employee.lastname,
                    address = employee.address
                )
            except Exception as e:
                logger.exception(e)
                db.rollback()
                db.close()
            finally:
                db.close()

    @strawberry.mutation
    def update_employee_password(self, employeeInfo: UpdatePasswordInputType) -> UpdatePasswordOutputType:

        with next(get_db()) as db:
            try:
                employee = authenticate_employee(db, employeeInfo.phone_number, employeeInfo.current_password)
                hashed_pwd = pwd_context.hash(employeeInfo.new_password)
                employee.password = hashed_pwd
                db.commit()
                db.refresh(employee)

                return UpdatePasswordOutputType(
                    success = "Password succesfuly updated"
                )
            except Exception as e:
                db.rollback()
                db.close()
                logger.exception(e)
            finally:
                db.close()

    @strawberry.mutation
    def create_visitor(self) -> str:

        return "create visitor"