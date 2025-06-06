import asyncio
from datetime import datetime, timedelta, timezone
import base64
from typing import List
import typing
import strawberry
from fastapi import Depends
from sqlalchemy.sql.coercions import expect
from strawberry.types import Info
from src.auth import create_token, get_current_user, oauth2_scheme
from src.components.resolvers import generate_report
from src.crud import pwd_context, authenticate_employee, count_attendance_percentage, total_employee_on_leave, \
    get_task_completion_percentage, get_visits_group_by_week_day, get_vehicle_group_by_week_day, \
    get_weekly_attendance_summary, create_conversation, accept_participate_event, deny_participate_event, \
    insert_message, get_event_by_user, \
    update_message_status, get_appointment_today_percentage
from src.database import get_db
from src.models import Employee, Role, EmployeeRole, Visit, Visitor
from src.schema.input_type import CreateEmployeeInput, CreateEmployeeRole, GenerateReportInput, UpdateEmployeeInput, UpdatePasswordInputType, \
    AddVisitorBrowserInputType, AttendanceInpuType, EmployeeId, CreateConvInput, ParticipantInput, MessageInput, \
    EventByUserInput, MessageStatusInput, EmployeeAppointmentId
from src import logger
from src.schema.output_type import EmployeeOnLeave, AttendnacePercentage, EmployeeCreationType, EmployeeType, GenerateReportPayload, \
    LoginReturnType, EmployeeUpdateType, ReportResult, \
    UpdatePasswordOutputType, DataType, CreateVisitorType, DayAttendanceType, EmployeeAttendatceType, AttendanceType, \
    DayAttendanceType, \
    TaskCompletionPercentage, VisitsCountByDay, VehicleCountByDay, AttendanceCountByWeek, CreateConvOutput, \
    AcceptParcipateEvent, DenyParcipateEvent, InsertMesaageOuput, EventWithUserParticipant, MessageStatusOutput, \
    AppointmentTodayPercentage
from src.utils import  generate_date_range, get_attendance_for_day, calculate_time_in_building
from typing import AsyncGenerator

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
    def get_employees(self) -> str:

        with next(get_db()) as db:
           query =  db.query(Visit).filter(Visit.host_employee == "862dcc85-ae68-46b3-ad03-1a7d59c57fca")
           for rows in query.all():
               print(rows.host_employee)

        return "done"
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

    @strawberry.field
    def get_report_attandance(self, input: AttendanceInpuType) -> List[DayAttendanceType]:
        date_range = list(generate_date_range(input.start_date, input.end_date))
        result = []
        fmt = "%H:%M:%S"
        def time_check(clock_in, clock_out):
            if clock_out is None:
                return None
            if clock_in.strftime(fmt) > clock_out.strftime(fmt):
                return datetime.strptime("15:00:00", fmt)
            return clock_out
        with next(get_db()) as db:
            for date in date_range:
                print(f"\nDate: {date.strftime('%Y-%m-%d')}")
                
                attendances = get_attendance_for_day(db, date)

                attendance_list = [
                    AttendanceType(
                        employee=EmployeeAttendatceType(id=att.employee.id, firstname=att.employee.firstname, lastname=att.employee.lastname),
                        clock_in=att.clock_in_time,
                        clock_out= time_check(att.clock_in_time , att.clock_out_time),
                        time_in_building = calculate_time_in_building(att.clock_in_time.strftime("%H:%M:%S"), att.clock_out_time.strftime("%H:%M:%S") if att.clock_out_time else None)
                    ) for att in attendances
                ]

                result.append(DayAttendanceType(date=date, attendance=attendance_list))
            return result

    @strawberry.field
    def get_attendance_percentage(self) -> AttendnacePercentage:
        with next(get_db()) as db:
            try:
                result  = count_attendance_percentage(db)
                return result
            except Exception as e:
                logger.error(f"Error while calculating attendance percentage: {e}")
                raise e
            finally:
                db.close()

    @strawberry.field
    def get_total_employee_on_leave(self) -> EmployeeOnLeave:
        with next(get_db()) as db:
            try:
                leaves_employee = total_employee_on_leave(db)
                return leaves_employee
            except Exception as e:
                logger.exception(e)
                raise Exception("Something went wrong: Internal server error")
            finally:
                db.close()

    @strawberry.field
    def get_visits_by_day(self) -> List[VisitsCountByDay]:
        with next(get_db()) as db:
            try:
                visits_by_day = get_visits_group_by_week_day(db)
                return visits_by_day
            except Exception as e:
                logger.exception(e)
                raise Exception("Something went wrong: Internal server error")
            finally:
                db.close()
    
    @strawberry.field
    def get_attendance_by_day(self) -> List[AttendanceCountByWeek]:
        with next(get_db()) as db:
            try:
                vehicle_by_day = get_weekly_attendance_summary(db)
                return vehicle_by_day
            except Exception as e:
                logger.exception(e)
                raise Exception("Something went wrong: Internal server error")
            finally:
                db.close()

    @strawberry.field
    def get_percentage_task(self, id: EmployeeId) -> TaskCompletionPercentage:

        with next(get_db()) as db:
            try:
                task_percentage = get_task_completion_percentage(db, id.id)
                return task_percentage
            except Exception as e:
                logger.exception(e)
                raise Exception("Something went wrong: Internal server error")
            finally:
                db.close()

    @strawberry.field
    def get_events_by_user(self, inputs: EventByUserInput) -> List[EventWithUserParticipant]:

        with next(get_db()) as db:
            try:
                result = get_event_by_user(db, inputs)
                return result
            except Exception as e:
                logger.exception(e)
                raise Exception(f'Internal server error {e}')
            finally:
                db.close()

    @strawberry.field
    def get_appointment_today_percent(self, employee: EmployeeAppointmentId) -> AppointmentTodayPercentage:

        with next(get_db()) as db:
            result = get_appointment_today_percentage(db, employee)

            return result





@strawberry.type
class Subscription:

    @strawberry.subscription
    async def get_report_attandance(self, input: AttendanceInpuType) -> List[DayAttendanceType]:
        date_range = list(generate_date_range(input.start_date, input.end_date))
        result = []
        fmt = "%H:%M:%S"
        attendance_list= []
        with next(get_db()) as db:
            for date in date_range:
                print(f"\nDate: {date.strftime('%Y-%m-%d')}")
                
                attendances = get_attendance_for_day(db, date)
                for att in attendances:
                    if att.clock_in_time() > att.clock_out_time():
                        print(f"{att.employee.firstname} - {att.employee.lastname}")
                    print("Not founded")
                    attendance_list.append(
                        AttendanceType(
                            employee=EmployeeAttendatceType(id=att.employee.id, firstname=att.employee.firstname, lastname=att.employee.lastname),
                            clock_in=att.clock_in_time,
                            clock_out=  "15:00:00" if att.clock_in_time() > att.clock_out_time() else att.clock_out_time ,
                            time_in_building = calculate_time_in_building(att.clock_in_time.strftime("%H:%M:%S"), att.clock_out_time.strftime("%H:%M:%S") if att.clock_out_time else None)
                        ) 
                    )

                result.append(DayAttendanceType(date=date, attendance=attendance_list))
            return result
    
    @strawberry.subscription
    async def get_attendance_percentage(self) -> AsyncGenerator[AttendnacePercentage, None]:
        with next(get_db()) as db:
            while True:
                try:
                    result  = count_attendance_percentage(db)
                    yield result
                    await asyncio.sleep(5)
                except Exception as e:
                    logger.error(f"Error while calculating attendance percentage: {e}")
                    raise e
                finally:
                    db.close()

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
                
                elif employee.roles == CreateEmployeeRole.GUARD:
                    guard_role = db.query(Role).filter_by(role_name="GUARD").one()
                    employee_role_3 = EmployeeRole(employee_id=db_employee.id, role_id=guard_role.id)
                    db.add_all([employee_role_1, employee_role_3])
                    db.commit()
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
                if db.query(Employee).filter(Employee.phone_number == employee.phone_number).first() and user.phone_number != employee.phone_number :
                    raise Exception("Someone with this phone number exist already")
                user.phone_number = employee.phone_number if employee.phone_number else user.phone_number

                db.commit()
                return EmployeeUpdateType(
                    id=user.id,
                    firstname=user.firstname,
                    lastname=user.lastname,
                    address = user.address,
                    phone_number=user.phone_number
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
                employee.password_change_at = datetime.now()
                db.commit()
                db.refresh(employee)

                return UpdatePasswordOutputType(
                    success = "Password successfully updated"
                )
            except Exception as e:

                db.rollback()
                db.close()
                logger.exception(e)
                raise Exception(f"Internal error: {e}")
            finally:
                db.close()

    @strawberry.mutation
    def create_visitor(self, visitor: AddVisitorBrowserInputType) -> CreateVisitorType:

        if visitor.visitor :
            if not visitor.host_service and not visitor.host_employee and not visitor.host_department:
                raise Exception(" No services nor department nor employee has been chosen for the visit ")
            with next(get_db()) as db:
                try:
                    db_visit = Visit(
                        host_employee = visitor.host_employee,
                        host_department= visitor.host_department,
                        host_service = visitor.host_service,
                        visitor = visitor.visitor,
                        vehicle = visitor.vehicle,
                        status = visitor.status,
                        reason = visitor.reason,
                        reg_no = visitor.reg_no
                    )

                    db.add(db_visit)
                    db.commit()
                    return CreateVisitorType(id = db_visit.id)
                except Exception as e:
                    db.rollback()
                    db.close()
                    logger.exception(e)
                finally:
                    db.close()

        elif not visitor.visitor:
            if not visitor.host_service and not visitor.host_employee and not visitor.host_department:
                raise Exception(" No services nor department nor employee has been chosen for the visit ")
            with next(get_db()) as db:
                try:
                    db_visitor = Visitor(
                        firstname = visitor.firstname,
                        lastname = visitor.lastname,
                        company_id = visitor.company_id,
                        id_number = visitor.id_number,
                        phone_number = visitor.phone_number
                    )
                    db.add(db_visitor)
                    db.commit()

                    db_visit = Visit(
                        host_employee=visitor.host_employee,
                        host_department=visitor.host_department,
                        host_service=visitor.host_service,
                        visitor=db_visitor.id,
                        vehicle=visitor.vehicle,
                        status=visitor.status,
                        reason=visitor.reason,
                        reg_no=visitor.reg_no
                    )
                    db.add(db_visit)
                    db.commit()
                    return CreateVisitorType(id=db_visit.id)
                except Exception as e:
                    db.rollback()
                    db.close()
                    logger.exception(e)
                finally:
                    db.close()

    @strawberry.mutation
    def create_conversation(self, conversation: CreateConvInput) -> CreateConvOutput:

        with next(get_db()) as db:
            result = create_conversation(db, conversation)

            return result


    @strawberry.mutation
    def accept_participate_events(self, participant: ParticipantInput) -> AcceptParcipateEvent:

        with next(get_db()) as db:
            result = accept_participate_event(db, participant)

            return result


    @strawberry.mutation
    def decline_participate_events(self, participant: ParticipantInput) -> DenyParcipateEvent:
        with next(get_db()) as db:
            result = deny_participate_event(db, participant)

            return result

    @strawberry.mutation
    def add_message(self, inputs: MessageInput) -> InsertMesaageOuput:
        with next(get_db()) as db:
            result = insert_message(db, inputs)

            return result

    @strawberry.mutation
    def update_message_status(self, message_ids: MessageStatusInput) -> MessageStatusOutput:

        with next(get_db()) as db:
            result = update_message_status(db, message_ids)

            return result
    
    @strawberry.mutation
    def generate_csv_report(self, info: Info, input: GenerateReportInput) -> ReportResult:
        with next(get_db()) as db:
            try:
                reports = generate_report(
                report_type=input.report_type.value,
                category=input.category.value,
                category_id=input.category_id,
                from_date=input.from_date,
                to_date=input.to_date,
                db= db
            )
            except Exception as e:
                logger.error(f"{e}")
                db.rollback()
                db.close()
            finally:
                db.close()
            return reports