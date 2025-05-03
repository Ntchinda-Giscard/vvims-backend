import csv
import os
import uuid
from datetime import date
from sqlalchemy.orm import Session
from src.database import SessionLocal, get_db
from src.models import Visit, Attendance, Employee

REPORT_DIR = '/app/uploads'
os.makedirs(REPORT_DIR, exist_ok=True)

def generate_report(report_type: str, category: str, category_id: uuid.UUID, from_date: date, to_date: date, db: Session):

    if report_type == "visits":
        query = db.query(Visit)

        date_field = Visit.date
    else:
        query = db.query(Attendance)
        date_field = Attendance.clock_in_date
    
    query = query.filter(date_field >= from_date, date_field <= to_date)

    if category == "department":
        if report_type == "visits":
            query = query.filter(Visit.host_department == category_id)
        else:
            query = query.filter(Attendance.employee).filter(Employee.department_id == category_id)
    elif category == "service":
        if report_type == "visits":
            query = query.filter(Visit.host_service == category_id)
        else:
            query = query.join(Attendance.employee).filter(Employee.service_id == category_id)
    else:
        if report_type == "visits":
            query = query.filter(Visit.host_employee == category_id)
        else:
            query = query.filter(Attendance.employee_id == category_id)
    
    rows = query.all()
    filename = f"{report_type}_{category}_{category_id}_{from_date}_{to_date}.csv"
    filepath = os.path.join(REPORT_DIR, filename)

    with open(filepath, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        if report_type == "visits":
            writer.writerow(["Visitor Name", "Date", "Check In", "Check Out", "Reason", "Status"])
            for v in rows:
                writer.writerow([
                    f"{v.visitors.firstname} {v.visitors.lastname}",
                    v.date,
                    v.check_in_at,
                    v.check_out_at,
                    v.reason,
                    v.status
                ])
        else:
            writer.writerow(["Employee", "Date", "Clock In", "Clock Out", "Late"])
            for a in rows:
                writer.writerow([
                    f"{a.employee.firstname} {a.employee.lastname}",
                    a.clock_in_date,
                    a.clock_in_time,
                    a.clock_out_time,
                    getattr(a.attendance_state, 'is_late', False),
                ])
    
    return  f"http://172.17.15.28:30088/uploads/{filename}", filename