import calendar
from typing import Any, Optional
from passlib.context import CryptContext
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from sqlalchemy import func, cast, Date, Time, Numeric, select, case
from src import logger
from src.models import Employee, EmployeeRole, Role, Position, Attendance, Leave, Task, TaskStatusEnum, TaskStatus, \
    Visit, Vehicle, AttendanceState, Conversation, EmployeeConversation, ParticipantStatus, EventParticipant, Message, \
    MessageStatus, Event, MessageStatuses, Appointment, Department
from src.schema.output_type import EmployeeType, AttendnacePercentage, EmployeeOnLeave, TaskCompletionPercentage, \
    VisitsCountByDay, VehicleCountByDay, AttendanceCountByWeek, CreateConvOutput, AcceptParcipateEvent, \
    DenyParcipateEvent, InsertMesaageOuput, EventWithUserParticipant, EventType, ParticipantType, MessageStatusOutput, \
    AppointmentTodayPercentage
from src.schema.input_type import CreateEmployeeInput, CreateEmployeeRole, UpdateEmployeeInput, UpdatePasswordInputType, \
    EmployeeId, CreateConvInput, ParticipantInput, MessageInput, EventByUserInput, MessageStatusInput, \
    EmployeeAppointmentId
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


    if not employee:
        raise Exception(f'Employee not found with phone number {phone_number}')
    if not pwd_context.verify(password, employee.password):
        raise Exception('Incorrect password')

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
        return AttendnacePercentage(total_employees=0, attendance_percentage=0.0)

    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    last_24_hours = datetime.now() - timedelta(hours=24)#
    attendance_count = db.query(Attendance).filter(Attendance.clock_in_time >= today_start).count()


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
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate the start of the week (Monday) and end of the week (Sunday)
    start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
    end_of_week = start_of_week + timedelta(days=6)          # Sunday of this week

    # Step 1: Query the visitor data and group by day, ignoring the time part
    visitor_data = (
        db.query(
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
    print(visitor_data)
    # Step 2: Convert query results to a dictionary with date as key
    visitor_counts_by_day = {
        day.visit_day: day.visitor_count for day in visitor_data
    }
    print(visitor_counts_by_day)

    # Step 3: Generate the full week with default visitor count of 0 for missing days
    week = [ (start_of_week + timedelta(days=i)).date()
        for i in range(7)  # 7 days in a week
    ]

    print(week)
    full_week = [
        VisitsCountByDay(
            visit_day=(start_of_week + timedelta(days=i)).strftime("%A"),
            visitor_count=visitor_counts_by_day.get((start_of_week + timedelta(days=i)).date(), 0)
        )
        for i in range(7)  # 7 days in a week
    ]

    return full_week


def get_vehicle_group_by_week_day(db: Session) -> List[VehicleCountByDay]:
    """
    Counts the number of visits made by employees in each weekday group (Sunday, Monday, Tuesday, Wednesday, Thursday, Friday, Saturday).
    :param db: A database session instance used to interact with the database.
    :return: A list of dictionaries, each containing the weekday group name and the number of visits made by employees in that group.
    """
    
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate the start of the week (Monday) and end of the week (Sunday)
    start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
    end_of_week = start_of_week + timedelta(days=6)          # Sunday of this week

    # Step 1: Query the visitor data and group by day, ignoring the time part
    vehicle_data = (
        db.query(
            func.date(Vehicle.created_at).label("vehicle_day"),  # Stripping the time part
            func.count(Vehicle.id).label("vehicle_count")
        )
        .filter(
            func.date(Vehicle.created_at) >= start_of_week.date(),  # Ensure both sides are date-only
            func.date(Vehicle.created_at) <= end_of_week.date()
        )
        .group_by(func.date(Visit.date))
        .all()
    )
    print(vehicle_data)
    # Step 2: Convert query results to a dictionary with date as key
    vehicle_counts_by_day = {
        day.vehicle_day: day.vehicle_count for day in vehicle_data
    }
    print(vehicle_counts_by_day)

    # Step 3: Generate the full week with default visitor count of 0 for missing days
    week = [ (start_of_week + timedelta(days=i)).date()
        for i in range(7)  # 7 days in a week
    ]

    print(week)
    full_week = [
        VehicleCountByDay(
            visit_day=(start_of_week + timedelta(days=i)).strftime("%A"),
            visitor_count=vehicle_counts_by_day.get((start_of_week + timedelta(days=i)).date(), 0)
        )
        for i in range(7)  # 7 days in a week
    ]

    return full_week


def get_weekly_attendance_summary(session) -> List[AttendanceCountByWeek]:
    # Calculate the start and end of the current week (Monday to Sunday)
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # Calculate the start of the week (Monday) and end of the week (Sunday)
    start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
    end_of_week = start_of_week + timedelta(days=6)          # Sunday of this week

    # Query to group by day of the week
    attendance_summary = (
        session.query(
            ((func.extract('dow', Attendance.clock_in_date) + 6) % 7).label('weekday'),  # Alias as 'weekday'
            func.count(Attendance.id).label('present_count'),
            func.count(case((AttendanceState.is_late == False, 1), else_=None)).label('on_time_count'),
            func.count(case((AttendanceState.is_late == True, 1), else_=None)).label('late_count'),
        )
        .join(AttendanceState, AttendanceState.attendance_id == Attendance.id, isouter=True)
        .filter(Attendance.clock_in_date >= start_of_week, Attendance.clock_in_date <= end_of_week)
        .group_by('weekday')  # Use the alias here
        .order_by('weekday')  # Use the alias here
        .all()
    )

    # Initialize a dictionary with zero values for each day of the week (0=Monday, 6=Sunday)
    week_data = {i: {"present_count": 0, "on_time_count": 0, "late_count": 0} for i in range(7)}

    # Populate the dictionary with actual query results
    for day in attendance_summary:
        week_data[int(day.weekday)] = {
            "present_count": day.present_count,
            "on_time_count": day.on_time_count,
            "late_count": day.late_count,
        }

    # Format the result with day names
    result = [
        AttendanceCountByWeek(
            day=calendar.day_name[weekday],  # Get the name of the day (e.g., "Monday")
            present_employees=week_data[weekday]["present_count"],
            on_time_employees=week_data[weekday]["on_time_count"],
            late_employees=week_data[weekday]["late_count"],
        )
        for weekday in range(7)
    ]
    
    return result


def create_conversation(db: Session, conv_input: CreateConvInput) -> CreateConvOutput:
    try:

        existing_conversation = (
            db.query(Conversation)
            .join(EmployeeConversation, EmployeeConversation.conversation_id == Conversation.id)
            .filter(
                Conversation.is_group == False,
                EmployeeConversation.employee_id.in_([conv_input.first_participant, conv_input.second_participants])
            )
            .group_by(Conversation.id)
            .having(func.count(EmployeeConversation.employee_id) == 2)  # Ensure both participants are present
            .first()
        )

        if existing_conversation:
            return CreateConvOutput(id=existing_conversation.id)

        conv = Conversation(
            name = conv_input.name,
            is_group = conv_input.is_group
        )

        print("Conversation id", conv.id)

        db.add(conv)
        db.commit()

        f_participants = EmployeeConversation(
            employee_id= conv_input.first_participant,
            conversation_id = conv.id
        )

        db.add(f_participants)

        s_participants = EmployeeConversation(
            employee_id= conv_input.second_participants,
            conversation_id = conv.id
        )

        db.add(s_participants)

        db.commit()

        return CreateConvOutput(id=conv.id)
    except Exception as e:
        logger.exception(e)
        db.rollback()
        db.close()
        raise Exception(f'{e}')
    finally:
        db.close()


def accept_participate_event(db: Session, participant: ParticipantInput) -> AcceptParcipateEvent:

    try:
        participant = db.query(EventParticipant).filter(EventParticipant.id == participant.id).first()
        participant.status = ParticipantStatus.COMPLETED
        db.commit()

        return AcceptParcipateEvent(id = participant.id)
    except Exception as e:
        logger.exception(e)
        raise Exception(f'Internal server error: {e}')
    finally:
        db.close()

def deny_participate_event(db: Session, participant: ParticipantInput) -> DenyParcipateEvent:
    try:
        participant = db.query(EventParticipant).filter(EventParticipant.id == participant.id).first()
        participant.status = ParticipantStatus.ON_GOING
        db.commit()

        return DenyParcipateEvent(id=participant.id)
    except Exception as e:
        logger.exception(e)
        raise Exception(f'Internal server error: {e}')
    finally:
        db.close()


def insert_message(db: Session, message: MessageInput) -> InsertMesaageOuput:
    try:
        message_input = Message(
            sender_id = message.employee_id,
            conversation_id = message.conversation_id,
            content = message.content
        )

        db.add(message_input)

        message_status = MessageStatus(
            employee_id = message.employee_id,
            message_id = message_input.id
        )

        db.add(message_status)

        db.commit()

        return InsertMesaageOuput(
            id = message_input.id
        )
    except Exception as e:
        logger.exception(e)
        raise Exception(f'Internal server error {e}')
    finally:
        db.close()


def get_event_by_user(db: Session, inputs: EventByUserInput) -> List[EventWithUserParticipant]:
    user_events_query = (
        db.query(Event.id)
        .join(EventParticipant, Event.id == EventParticipant.event_id)
        .filter(
            Event.start_date == inputs.date,
            EventParticipant.employee_id == inputs.employee_id,
            EventParticipant.status == ParticipantStatus.COMPLETED
        )
    )

    events_ids = [event.id for event in user_events_query.all()]

    query_participants = (
        db.query(Event, EventParticipant, Employee)
        .join(EventParticipant, Event.id == EventParticipant.event_id)
        .join(Employee, EventParticipant.employee_id == Employee.id)
        .filter(
            Event.id.in_(events_ids),
            EventParticipant.status == ParticipantStatus.COMPLETED
        )
        .order_by(desc(Event.start_date))
    )

    results = query_participants.all()

    events_with_participants = {}
    for event, participant, employee in results:
        if event.id not in events_with_participants:
            events_with_participants[event.id] = {
                'event': EventType( date=f'{event.start_date}', title=event.title, start_time=f'{event.start_time}', end_time= f'{event.end_time}', description= f'{event.description}'),
                'participants': []
            }

        events_with_participants[event.id]['participants'].append(
            ParticipantType(
                firstname= employee.firstname,
                lastname= employee.lastname
            )
        )

    return [
        EventWithUserParticipant(
            event = data['event'],
            participant = data['participants']
        ) for data in events_with_participants.values()
    ]


def update_message_status(db: Session, message_ids: MessageStatusInput) -> MessageStatusOutput:

    statuses = {
        'DELIVERED': MessageStatuses.DELIVERED,
        'SEEN': MessageStatuses.SEEN
    }
    try:
        for message_id in message_ids.id:
            message_status = (
                db.query(MessageStatus)
                .filter(MessageStatus.message_id == message_id)
                .first()
            )
            print("Current message status ======>", message_status.status)
            print("Updated message status ======>", message_ids.status)
            message_status.status = statuses[message_ids.status]
        db.commit()
        return MessageStatusOutput(state=message_ids.status)
    except Exception as e:
        logger.exception(e)
        raise Exception(f"Internal server error: {e}")
    finally:
        db.close()



def get_appointment_today_percentage(db: Session, employee: EmployeeAppointmentId) -> AppointmentTodayPercentage:

    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_starts = today_start + timedelta(days=1)
        tomorrow_end = tomorrow_starts + timedelta(days=1)

        todays_count = (
            db.query(func.count(Appointment.id))
            .filter(Appointment.employee_id==employee.id, Appointment.date >= today_start, Appointment.date < tomorrow_starts)
            .scalar()
        )

        print("Todays count ====>:", todays_count)

        tomorrow_count = (
            db.query(func.count(Appointment.id))
            .filter(Appointment.date >= tomorrow_starts, Appointment.date < tomorrow_end)
            .scalar()
        )

        print("Tomorrow's count ====>:", tomorrow_count)

        if todays_count == 0:
            return AppointmentTodayPercentage(today_count=0, tomorrow_count=tomorrow_count, percent=None)
        percentage = ((todays_count - tomorrow_count)/todays_count)*100
        return AppointmentTodayPercentage(today_count=todays_count, tomorrow_count=tomorrow_count, percent= round(percentage, 1))

    except Exception as e:
        logger.exception(e)
        raise Exception(f"Internal server error {e}")
    finally:
        db.close()


def get_employee_attendance_summary(db: Session, employee: Employee, attendance: Attendance):
    start_date = '2025-02-01'
    end_date = '2025-02-28'
    query = (
        db.query(
            Employee.id,
            Employee.firstname,
            func.count(Attendance.id).label('present_count'),
            cast(
                func.to_char(
                    func.to_timestamp(
                        func.avg(
                            func.extract('epoch', Attendance.clock_in_time)
                        )
                    ),
                    'HH24:MI:SS'
                ),
                Time
            ).label('avg_clock_in_time')
        )
        .join(Attendance, Employee.id == Attendance.employee_id)
        .filter(Attendance.clock_in_date.between(start_date, end_date))
        .group_by(Employee.id, Employee.firstname)
    )

    result = query.all()

    # Convert result tuples to list of dictionaries
    result_dicts = [
        {
            'id': res.id,
            'name': res.firstname,
            'present': res.present_count,
            'avr_hrs': res.avg_clock_in_time
        }
        for res in result
    ]

    return result_dicts


def get_department_attendance_summary(db: Session, dept: Department):

    total_working_days_subquery = (
        db.query(func.count(func.distinct(Attendance.clock_in_date)).label('total_working_days'))
    ).subquery()

    # Main query to calculate attendance percentage by department
    query = (
        db.query(
            Department.id.label('department_id'),
            Department.name.label('department_name'),
            func.count(Attendance.id).label('total_attendances'),
            func.count(func.distinct(Employee.id)).label('total_employees'),
            cast(
                case(
                    (func.count(func.distinct(Employee.id)) == 0, 0),
                    else_=(func.count(Attendance.id) * 100.0) / (
                        func.count(func.distinct(Employee.id)) * total_working_days_subquery.c.total_working_days
                    )
                ),
                Numeric(5, 1)
            ).label('attendance_percentage')
        )
        .outerjoin(Employee, Department.id == Employee.department_id)
        .outerjoin(Attendance, Employee.id == Attendance.employee_id)
        .group_by(Department.id, Department.name, total_working_days_subquery.c.total_working_days)
    )

    # Execute the query
    result = query.all()

    # Process the result
    attendance_data = [
        {
            'department_id': row.department_id,
            'department_name': row.department_name,
            'attendance_percentage': row.attendance_percentage
        }
        for row in result
    ]

    return attendance_data