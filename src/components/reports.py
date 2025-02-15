from jinja2 import Environment, FileSystemLoader
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

env = Environment(loader=FileSystemLoader("template"))

class ReportGeneratorStrategy(ABC):

    @abstractmethod
    def render_html(self):
        return NotImplementedError

    @abstractmethod
    def generate_pdf(self):
        return NotImplementedError



class VisitsReportGenerator(ReportGeneratorStrategy):

    def __init__(self, Employee, Attendance):
        pass

    def render_html(self):
        return render_html(self.report_data, self.data_dept, self.summary, self.company_name)

    def generate_pdf(self):
        return generate_pdf(self.report_data, self.data_dept, self.summary, self.company_name)


class AttendanceReportGenerator(ReportGeneratorStrategy):

    def __init__(self, Employee, Attendance, Department):
        self.template = env.get_template("reports.html")
        self.employee = Employee
        self.attendance = Attendance
        self.department = Department
        

    def report_crud(self):
        summary = {}
        with next(get_db())as db:
            report_data = get_employee_attendance_summary(db, self.employee, self.attendance)
            data_dept = get_department_attendance_summary(db, self.department)
            summary["arrival_time"] = average_compnay_arrival_time(db, self.attendance)
            summary["avr_office_hours"] = average_time_in_office(db, self.attendance)
            summary["overall_perc"] = "{:.1f}%".format(attendance_percentage(db, self.attendance, self.employee))
            company_name = get_company_name(db, Company, TextContent)

        return report_data, data_dept, summary, company_name
  
    def render_html(self):
        report_data, data_dept, summary, company_name = self.report_crud()
        rendered_html = self.template.render(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            data=report_data,
            data_dept = data_dept,
            summary = summary,
            company_name = company_name
        )

        return rendered_html

    def generate_pdf(self):
        report_data, data_dept, summary, company_name = self.report_crud()
        html_content = self.render_html(report_data, data_dept, summary, company_name)
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        return pdf_bytes



ReportType = { "visit": VisitsReportGenerator(Employee, Attendance),
    "attendance": AttendanceReportGenerator(Employee, Attendance, Department)
}
@dataclass
class ReportName:
    visit_report: str = "Visits Report"
    attendance_report: str = "Attendance Report"

class ReportGenetorContext:

    def __init__(self, strategy: ReportGeneratorStrategy):
        self.strategy = strategy

    def generate_report(self):
        return self.strategy.generate_pdf()

def upload_report_to_s3(pdf_data):
    pdf_buffer = io.BytesIO(pdf_bytes)
    # Generate the current timestamp and a random number
    now = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    random_number = str(random.randint(1, 99999)).zfill(5)

    s3.upload_fileobj(pdf_buffer, "vvims-visitor", f"report_{now}_{random_number}.pdf")
    s3_url = f"https://vvims-visitor.s3.eu-north-1.amazonaws.com/attendance_report_{now}_{random_number}.pdf"
    return s3_url



