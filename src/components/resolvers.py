import csv
import os
import uuid
from datetime import date, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import Leave, Report, Visit, Attendance, Employee, ReportTypes
from src.schema.output_type import AttendanceReportRow, ReportResult, VisitReportRow

REPORT_DIR = '/app/uploads'

# def generate_report(
#     report_type: str,
#     category: str,
#     category_id: uuid.UUID,
#     from_date: date,
#     to_date: date,
#     db: Session = None
# ):
#     session: Session = db or SessionLocal()

#     # Visits report
#     if report_type == "visits":
#         date_field = Visit.date
#         filters = [
#             date_field >= from_date,
#             date_field <= to_date
#         ]

#         if category == "department":
#             filters.append(Visit.host_department == category_id)
#         elif category == "service":
#             filters.append(Visit.host_service == category_id)
#         elif category == "employee":
#             filters.append(Visit.host_employee == category_id)

#         rows = session.query(Visit).filter(*filters).all()

#         filename = f"visits_{category}_{category_id}_{from_date}_{to_date}.csv"
#         filepath = Path(REPORT_DIR) / filename
#         with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
#             writer = csv.writer(csvfile)
#             writer.writerow(["Visitor Name", "Date", "Check In", "Check Out", "Reason", "Status"])
#             for v in rows:
#                 writer.writerow([
#                     f"{v.visitors.firstname} {v.visitors.lastname}",
#                     v.date.isoformat(),
#                     v.check_in_at.isoformat() if v.check_in_at else '',
#                     v.check_out_at.isoformat() if v.check_out_at else '',
#                     v.reason or '',
#                     v.status or '',
#                 ])

#     # Attendance report
#     else:
#         emp_q = session.query(Employee)
#         if category == "department":
#             emp_q = emp_q.filter(Employee.department_id == category_id)
#         elif category == "service":
#             emp_q = emp_q.filter(Employee.service_id == category_id)
#         else:
#             emp_q = emp_q.filter(Employee.id == category_id)
#         employees = emp_q.all()

#         attendances = session.query(Attendance).filter(
#             Attendance.clock_in_date >= from_date,
#             Attendance.clock_in_date <= to_date
#         ).all()

#         leaves = session.query(
#             Leave.employee_id,
#             Leave.start_date,
#             Leave.end_date,
#             Leave.comment
#         ).filter(
#             Leave.start_date <= to_date,
#             Leave.end_date >= from_date
#         ).all()

#         filename = f"attendance_{category}_{category_id}_{from_date}_{to_date}.csv"
#         filepath = Path(REPORT_DIR) / filename
#         with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
#             writer = csv.writer(csvfile)
#             writer.writerow(["Employee", "Date", "Status", "Arrival", "Departure", "Late", "Reason"])

#             curr = from_date
#             while curr <= to_date:
#                 for emp in employees:
#                     att = next((a for a in attendances if a.employee_id == emp.id and a.clock_in_date == curr), None)
#                     lv = next((e for e in leaves if e[0] == emp.id and e[1] <= curr <= e[2]), None)

#                     if att:
#                         status = 'Present'
#                         arrival = att.clock_in_time.isoformat() if att.clock_in_time else ''
#                         departure = att.clock_out_time.isoformat() if att.clock_out_time else ''
#                         late = getattr(att.attendance_state, 'is_late', False)
#                         reason = ''
#                     elif lv:
#                         status = 'On Leave'
#                         arrival = ''
#                         departure = ''
#                         late = ''
#                         reason = lv[3] or ''
#                     else:
#                         status = 'Absent'
#                         arrival = ''
#                         departure = ''
#                         late = ''
#                         reason = ''

#                     writer.writerow([
#                         f"{emp.firstname} {emp.lastname}",
#                         curr.isoformat(),
#                         status,
#                         arrival,
#                         departure,
#                         late,
#                         reason
#                     ])
#                 curr += timedelta(days=1)

#     public_url = f"http://172.17.15.28:30088/uploads/{filename}"
#     report_enum = ReportTypes.ATTENDANCE if report_type == "attendance" else ReportTypes.VISITS

#     reports = Report(
#         report_link=public_url,
#         from_date=from_date,
#         to_date=to_date,
#         name=category,
#         types=report_enum
#     )
#     db.add(reports)
#     db.commit()
#     db.refresh(reports)

#     return public_url, filename

def generate_report(
    report_type: str,
    category: str,
    category_id: uuid.UUID,
    from_date: date,
    to_date: date,
    db: Session = None
) -> ReportResult:
    session: Session = db or SessionLocal()

    if report_type == "visits":
        filters = [
            Visit.date >= from_date,
            Visit.date <= to_date
        ]

        if category == "department":
            filters.append(Visit.host_department == category_id)
        elif category == "service":
            filters.append(Visit.host_service == category_id)
        elif category == "employee":
            filters.append(Visit.host_employee == category_id)

        rows = session.query(Visit).filter(*filters).all()

        data = [
            VisitReportRow(
                visitor_name=f"{v.visitors.firstname} {v.visitors.lastname}",
                date=v.date.isoformat(),
                check_in=v.check_in_at.isoformat() if v.check_in_at else None,
                check_out=v.check_out_at.isoformat() if v.check_out_at else None,
                reason=v.reason,
                status=v.status
            )
            for v in rows
        ]

        return ReportResult(type="visits", visit_data=data)

    else:
        emp_q = session.query(Employee)
        if category == "department":
            emp_q = emp_q.filter(Employee.department_id == category_id)
        elif category == "service":
            emp_q = emp_q.filter(Employee.service_id == category_id)
        else:
            emp_q = emp_q.filter(Employee.id == category_id)

        employees = emp_q.all()

        attendances = session.query(Attendance).filter(
            Attendance.clock_in_date >= from_date,
            Attendance.clock_in_date <= to_date
        ).all()

        leaves = session.query(
            Leave.employee_id,
            Leave.start_date,
            Leave.end_date,
            Leave.comment
        ).filter(
            Leave.start_date <= to_date,
            Leave.end_date >= from_date
        ).all()

        data = []
        curr = from_date
        while curr <= to_date:
            for emp in employees:
                att = next((a for a in attendances if a.employee_id == emp.id and a.clock_in_date == curr), None)
                lv = next((e for e in leaves if e[0] == emp.id and e[1] <= curr <= e[2]), None)

                if att:
                    status = 'Present'
                    arrival = att.clock_in_time.isoformat() if att.clock_in_time else None
                    departure = att.clock_out_time.isoformat() if att.clock_out_time else None
                    late = getattr(att.attendance_state, 'is_late', False)
                    reason = None
                elif lv:
                    status = 'On Leave'
                    arrival = None
                    departure = None
                    late = None
                    reason = lv[3] or None
                else:
                    status = 'Absent'
                    arrival = None
                    departure = None
                    late = None
                    reason = None

                data.append(AttendanceReportRow(
                    employee=f"{emp.firstname} {emp.lastname}",
                    date=curr.isoformat(),
                    status=status,
                    arrival=arrival,
                    departure=departure,
                    late=late,
                    reason=reason
                ))

            curr += timedelta(days=1)

        return ReportResult(type="attendance", attendance_data=data)
