import os
from dataclasses import dataclass
import base64
import boto3
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from abc import ABC, abstractmethod


# Set up Jinja2 environment (assuming your templates are in the "templates" folder)
env = Environment(loader=FileSystemLoader("template"))

def generate_chart():
    """Generate a Matplotlib bar chart and return it as a base64-encoded PNG."""
    # Sample attendance data for charting
    attendance_data = {
        "John Doe": 20,
        "Jane Smith": 18,
        "Michael Brown": 22,
        "Emily Davis": 15,
        "Daniel Lee": 19
    }

    names = list(attendance_data.keys())
    values = list(attendance_data.values())

    plt.figure(figsize=(6, 4))
    plt.bar(names, values, color="skyblue")
    plt.xlabel("Employees")
    plt.ylabel("Days Present")
    plt.title("Employee Attendance")
    plt.xticks(rotation=30)

    buf = BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    
    return base64.b64encode(buf.read()).decode("utf-8")

def render_html(report_data, data_dept, summary, company_name):
    """Render the HTML report using Jinja2 with embedded data and chart."""
    template = env.get_template("reports.html")
    
    rendered_html = template.render(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data=report_data,
        # chart=generate_chart(),
        data_dept = data_dept,
        summary = summary,
        company_name = company_name
    )
    return rendered_html

def generate_pdf(report_data, data_dept, summary, company_name):
    """Convert the rendered HTML to a PDF and return the PDF bytes."""
    html_content = render_html(report_data, data_dept, summary, company_name)
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes


class ReportGeneratorStrategy(ABC):

    @abstractmethod
    def render_html(self):
        return NotImplementedError

    @abstractmethod
    def generate_pdf(self):
        return NotImplementedError

    @abstractmethod
    def generate_report(self):
        return NotImplementedError


class VisitsReportGenerator(ReportGeneratorStrategy):

    def __init__(self, report_data, data_dept, summary, company_name):
        self.report_data = report_data
        self.data_dept = data_dept
        self.summary = summary
        self.company_name = company_name

    def render_html(self):
        return render_html(self.report_data, self.data_dept, self.summary, self.company_name)

    def generate_pdf(self):
        return generate_pdf(self.report_data, self.data_dept, self.summary, self.company_name)

    def generate_report(self):
        return self.generate_pdf()

class AttendanceReportGenerator(ReportGeneratorStrategy):

    def __init__(self, report_data, data_dept, summary, company_name):
        self.report_data = report_data
        self.data_dept = data_dept
        self.summary = summary
        self.company_name = company_name

    def render_html(self):
        return render_html(self.report_data, self.data_dept, self.summary, self.company_name)

    def generate_pdf(self):
        return generate_pdf(self.report_data, self.data_dept, self.summary, self.company_name)

    def generate_report(self):
        return self.generate_pdf()


class ReportGenetorContext:

    def __init__(self, strategy: ReportGeneratorStrategy):
        self.strategy = strategy

    def generate_report(self):
        return self.strategy.generate_report()



@dataclass
class Report:
    visit_report: ReportGeneratorStrategy = VisitsReportGenerator()
    attendance_report: ReportGeneratorStrategy = AttendanceReportGenerator()
