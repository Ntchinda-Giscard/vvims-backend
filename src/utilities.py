import os
import base64
import boto3
import matplotlib.pyplot as plt
from datetime import datetime
from io import BytesIO
from fastapi.responses import JSONResponse
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML


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

def render_html(report_data, data_dept, summary):
    """Render the HTML report using Jinja2 with embedded data and chart."""
    template = env.get_template("reports.html")
    
    # Sample table data for the report
    # report_data = [
    #     {"name": "John Doe", "present": 20, "avr_hrs": 98},
    #     {"name": "Jane Smith", "present": 18, "avr_hrs": 98},
    #     {"name": "Michael Brown", "present": 22, "avr_hrs": 98},
    # ]
    
    rendered_html = template.render(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data=report_data,
        chart=generate_chart(),
        data_dept = data_dept,
        summary = summary
    )
    return rendered_html

def generate_pdf(report_data, data_dept, summary):
    """Convert the rendered HTML to a PDF and return the PDF bytes."""
    html_content = render_html(report_data, data_dept, summary)
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes


