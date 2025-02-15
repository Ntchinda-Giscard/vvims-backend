from jinja2 import Environment, FileSystemLoader
from src.crud import (
    average_time_in_office,
    attendance_percentage,
    get_company_name,
    get_employee_attendance_summary,
    get_department_attendance_summary
)
from src.models import Employee, Attendance
from src.database import get_db
from abd import ABC, abstractmethod

env = Environment(loader=FileSystemLoader("template"))

class ReportGeneratorStrategy(ABC):

    @abstractmethod
    def render_html(self):
        return NotImplementedError

    @abstractmethod
    def generate_pdf(self):
        return NotImplementedError



class VisitsReportGenerator(ReportGeneratorStrategy):

    def __init__(self, db, Employee, Attendance):
        self.report_data = report_data
        self.data_dept = data_dept
        self.summary = summary
        self.company_name = company_name

    def render_html(self):
        return render_html(self.report_data, self.data_dept, self.summary, self.company_name)

    def generate_pdf(self):
        return generate_pdf(self.report_data, self.data_dept, self.summary, self.company_name)


class AttendanceReportGenerator(ReportGeneratorStrategy):

    def __init__(self, db, Employee, Attendance):
        self.template = env.get_template("reports.html")
        self.db = db
        self.employee = Employee
        self.attendance = Attendance
        

    def generate_report(self):
        summary = {}
        report_data = get_employee_attendance_summary(self.db, self.employee, self.attendance)
        data_dept = get_department_attendance_summary(self.db, self.employee, self.attendance)
        summary["arrival_time"] = average_compnay_arrival_time(self.db, self.attendance)
        summary["avr_office_hours"] = average_time_in_office(self.db, self.attendance)
        summary["overall_perc"] = "{:.1f}%".format(attendance_percentage(self.db, self.attendance, self.employee))
        company_name = get_company_name(self.db)

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


@dataclass
class Reports:
    visit_report: ReportGeneratorStrategy = VisitsReportGenerator(get_db(), Employee, Attendance)
    attendance_report: ReportGeneratorStrategy = AttendanceReportGenerator(get_db(), Employee, Attendance)

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



