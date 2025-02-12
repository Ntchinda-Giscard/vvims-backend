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
env = Environment(loader=FileSystemLoader("templates"))

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

def render_html():
    """Render the HTML report using Jinja2 with embedded data and chart."""
    template = env.get_template("template/reports.html")
    
    # Sample table data for the report
    report_data = [
        {"name": "John Doe", "present": 20, "absent": 5},
        {"name": "Jane Smith", "present": 18, "absent": 7},
        {"name": "Michael Brown", "present": 22, "absent": 3},
    ]
    
    rendered_html = template.render(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        data=report_data,
        chart=generate_chart()
    )
    return rendered_html

def generate_pdf():
    """Convert the rendered HTML to a PDF and return the PDF bytes."""
    html_content = render_html()
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes

@app.get("/generate-upload-pdf")
def generate_and_upload_pdf():
    """Generate the PDF report, upload it to AWS S3, and return the S3 URL."""
    pdf_bytes = generate_pdf()
    
    # Use BytesIO for the PDF file
    pdf_buffer = BytesIO(pdf_bytes)
    
    # Generate a unique S3 key using the current timestamp
    timestamp = datetime.now().strftime("%Y_%m_%d_%H:%M:%S")
    s3_key = f"reports/{timestamp}__{str(os.getpid()).zfill(5)}.pdf"
    
    # Upload PDF to S3
    s3_client.upload_fileobj(pdf_buffer, S3_BUCKET, s3_key, ExtraArgs={"ContentType": "application/pdf"})
    
    # Construct the S3 URL (adjust if your bucket has a different endpoint or is in a specific region)
    s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"
    
    return JSONResponse({"s3_url": s3_url})