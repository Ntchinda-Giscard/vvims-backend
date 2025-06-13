import csv
import os
import uuid
from datetime import date, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import Leave, Report, Visit, Attendance, Employee, ReportTypes
from src.schema.output_type import AttendanceReportRow, LeaveReportRow, ReportResult, VisitReportRow

REPORT_DIR = '/app/uploads'


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
    
    elif report_type == "leaves":
        emp_q = session.query(Employee)
        if category == "department":
            emp_q = emp_q.filter(Employee.department_id == category_id)
        elif category == "service":
            emp_q = emp_q.filter(Employee.service_id == category_id)
        else:
            emp_q = emp_q.filter(Employee.id == category_id)

        employees = emp_q.all()
        emp_ids = [e.id for e in employees]

        leaves = session.query(Leave).join(Employee).filter(
            Leave.employee_id.in_(emp_ids),
            Leave.start_date <= to_date,
            Leave.end_date >= from_date
        ).all()

        data = []
        for leave in leaves:
            data.append(LeaveReportRow(
                employee=f"{leave.employee.firstname} {leave.employee.lastname}",
                start_date=leave.start_date.isoformat(),
                end_date=leave.end_date.isoformat(),
                duration=(leave.end_date - leave.start_date).days + 1,
                reason=leave.comment
            ))

        return ReportResult(type="leaves", leave_data=data)


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