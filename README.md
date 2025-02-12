Generating a PDF Report from an HTML Webpage with Charts and Tables

You want to generate a PDF from an HTML template that includes tables, charts, and other elements. The best approach is: 1. Render your data into an HTML template (using Jinja2). 2. Generate charts dynamically (using Matplotlib). 3. Convert the HTML to a PDF (using WeasyPrint). 4. Provide a FastAPI endpoint to generate and serve the PDF for download.

1. Install Dependencies

Ensure you have the required Python packages:

pip install fastapi uvicorn jinja2 weasyprint matplotlib

    WeasyPrint may require additional system libraries like Cairo, Pango, and GDK-PixBuf. Check the WeasyPrint documentation for system requirements.

2. Create the HTML Template (templates/report.html)

Create a file at templates/report.html:

<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Attendance Report</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 20px; }
      h1 { text-align: center; }
      h2 { margin-top: 40px; }
      table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
      }
      table, th, td {
        border: 1px solid #ccc;
      }
      th, td {
        padding: 8px;
        text-align: center;
      }
      th {
        background-color: #f2f2f2;
      }
      .chart {
        text-align: center;
        margin-top: 20px;
      }
    </style>
  </head>
  <body>
    <h1>Attendance Report</h1>

    <h2>Summary Table</h2>
    <table>
      <thead>
        <tr>
          <th>Employee</th>
          <th>Present Days</th>
          <th>Absent Days</th>
          <th>On-time (%)</th>
        </tr>
      </thead>
      <tbody>
        {% for record in data %}
        <tr>
          <td>{{ record.name }}</td>
          <td>{{ record.present }}</td>
          <td>{{ record.absent }}</td>
          <td>{{ record.on_time_percentage }}%</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>

    <h2>Attendance Chart</h2>
    <div class="chart">
      <img src="data:image/png;base64,{{ chart }}" alt="Attendance Chart">
    </div>

  </body>
</html>

3. Create the FastAPI Backend

Now, create a FastAPI server to generate and return the PDF:

from fastapi import FastAPI, Response
from fastapi.responses import FileResponse
from jinja2 import Environment, FileSystemLoader
import weasyprint
import matplotlib.pyplot as plt
import io
import base64
import os
from datetime import datetime

app = FastAPI()

# Load Jinja2 environment

env = Environment(loader=FileSystemLoader("templates"))

# Sample data

attendance_data = [
{"name": "John Doe", "present": 20, "absent": 5, "on_time_percentage": 80},
{"name": "Jane Smith", "present": 18, "absent": 7, "on_time_percentage": 75},
{"name": "Michael Brown", "present": 22, "absent": 3, "on_time_percentage": 90},
]

def generate_chart():
"""Generate a sample attendance bar chart and return base64-encoded PNG."""
names = [d["name"] for d in attendance_data]
present_days = [d["present"] for d in attendance_data]

    plt.figure(figsize=(6, 4))
    plt.bar(names, present_days, color='blue')
    plt.xlabel("Employees")
    plt.ylabel("Present Days")
    plt.title("Attendance Summary")

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()

    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

@app.get("/generate-pdf")
def generate_pdf():
"""Generate a PDF from an HTML template and return it for download."""

    # Generate chart
    chart_base64 = generate_chart()

    # Render HTML with Jinja2
    template = env.get_template("report.html")
    html_content = template.render(data=attendance_data, chart=chart_base64)

    # Convert HTML to PDF
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()

    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y_%m_%d_%H:%M:%S")
    filename = f"attendance_report_{timestamp}.pdf"
    pdf_path = f"generated_pdfs/{filename}"

    # Ensure directory exists
    os.makedirs("generated_pdfs", exist_ok=True)

    # Save PDF
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    return FileResponse(pdf_path, filename=filename, media_type="application/pdf")

4. Run the FastAPI Server

Start your server:

uvicorn main:app --reload

5. Access the PDF Generation Endpoint

Visit in your browser:

http://127.0.0.1:8000/generate-pdf

Or use curl:

curl -O http://127.0.0.1:8000/generate-pdf

This will generate a PDF with a table and a chart and return it for download.

6. Upload to S3 (Optional)

If you want to upload the PDF to Amazon S3, install boto3:

pip install boto3

Modify the function to upload to S3:

import boto3

S3_BUCKET = "your-bucket-name"
S3_ACCESS_KEY = "your-access-key"
S3_SECRET_KEY = "your-secret-key"

s3_client = boto3.client(
"s3",
aws_access_key_id=S3_ACCESS_KEY,
aws_secret_access_key=S3_SECRET_KEY
)

@app.get("/upload-pdf")
def upload*pdf_to_s3():
timestamp = datetime.now().strftime("%Y*%m*%d*%H:%M:%S")
filename = f"attendance*report*{timestamp}.pdf"
pdf_path = f"generated_pdfs/{filename}"

    if not os.path.exists(pdf_path):
        return {"error": "PDF file not found"}

    s3_key = f"reports/{filename}"

    s3_client.upload_file(pdf_path, S3_BUCKET, s3_key)

    s3_url = f"https://{S3_BUCKET}.s3.amazonaws.com/{s3_key}"

    return {"url": s3_url}

7. Download the PDF from S3

After uploading, you can download it directly using the returned URL.

Summary

✔ Generate an HTML report with Jinja2
✔ Embed a Matplotlib chart as a base64 image
✔ Convert the HTML to PDF with WeasyPrint
✔ Expose a FastAPI endpoint to generate and serve the PDF
✔ (Optional) Upload the PDF to Amazon S3

This approach ensures a clean, automated way to generate and distribute attendance reports. Let me know if you need modifications!
