from weasyprint import HTML
from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from src.crud import (
    average_time_in_office,
    attendance_percentage,
    get_company_name,
    get_employee_attendance_summary,
    get_department_attendance_summary,
    average_compnay_arrival_time
)
from src.models import (
    Employee, Attendance, Department,
    Company, TextContent)
from src.database import get_db
from abc import ABC, abstractmethod
from dataclasses import dataclass
import boto3
import os
import io
import random


env = Environment(loader=FileSystemLoader("template"))
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY'),
    aws_secret_access_key=os.getenv('AWS_SECRET_KEY'),
    region_name='eu-north-1'
)

class ReportGeneratorStrategy(ABC):
    @abstractmethod
    def render_html(self):
        raise NotImplementedError

    @abstractmethod
    def generate_pdf(self):
        raise NotImplementedError

class VisitsReportGenerator(ReportGeneratorStrategy):
    def __init__(self, Employee, Attendance):
        # Implement initialization if needed
        pass

    def render_html(self):
        # Implement render_html for visits report
        pass

    def generate_pdf(self):
        # Implement generate_pdf for visits report
        pass

class AttendanceReportGenerator(ReportGeneratorStrategy):
    def __init__(self, Employee, Attendance, Department):
        self.template = env.get_template("reports.html")
        self.employee = Employee
        self.attendance = Attendance
        self.department = Department

    def report_crud(self):
        with next(get_db()) as db:
            report_data = get_employee_attendance_summary(db, self.employee, self.attendance)
            data_dept = get_department_attendance_summary(db, self.department)
            summary = {
                "arrival_time": average_compnay_arrival_time(db, self.attendance),
                "avr_office_hours": average_time_in_office(db, self.attendance),
                "overall_perc": "{:.1f}%".format(attendance_percentage(db, self.attendance, self.employee))
            }
            company_name = get_company_name(db, Company, TextContent)
        return report_data, data_dept, summary, company_name

    def render_html(self):
        report_data, data_dept, summary, company_name = self.report_crud()
        rendered_html = self.template.render(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data=report_data,
            data_dept=data_dept,
            summary=summary,
            company_name=company_name
        )
        return rendered_html

    def generate_pdf(self):
        html_content = self.render_html()
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes

ReportType = {
    "visit": VisitsReportGenerator(Employee, Attendance),
    "attendance": AttendanceReportGenerator(Employee, Attendance, Department)
}

ReportName = {
    "visit": "Visits Report",
    "attendance":  "Atendance Report"}

class ReportGeneratorContext:
    def __init__(self, strategy: ReportGeneratorStrategy):
        self.strategy = strategy

    def generate_report(self):
        return self.strategy.generate_pdf()

def upload_report_to_s3(pdf_data):
    pdf_buffer = io.BytesIO(pdf_data)
    now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    random_number = str(random.randint(1, 99999)).zfill(5)
    file_name = f"attendance_report_{now}_{random_number}.pdf"
    s3.upload_fileobj(pdf_buffer, "vvims-visitor", file_name)
    s3_url = f"https://vvims-visitor.s3.eu-north-1.amazonaws.com/{file_name}"
    return s3_url


