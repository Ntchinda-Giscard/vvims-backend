import requests

# Define the API endpoint
url = "https://ntchinda-giscard-vvims-backend.hf.space/api/v1/add-visits"

# Authorization header (replace with your actual token)
headers = {
    "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI1NWI0ZTM4ZC02ZDM1LTRhMTAtOTgxZS01YTBjMTNkNjAxZGYiLCJuYW1lIjoiZ3V5IGNzcCIsImlhdCI6MTc1OTU5NTY3MywiYWRtaW4iOnRydWUsImh0dHBzOi8vaGFzdXJhLmlvL2p3dC9jbGFpbXMiOnsieC1oYXN1cmEtYWxsb3dlZC1yb2xlcyI6WyJlbXBsb3llZSIsImFkbWluIl0sIngtaGFzdXJhLXJvbGUiOiJhZG1pbiIsIngtaGFzdXJhLXVzZXItaWQiOiI1NWI0ZTM4ZC02ZDM1LTRhMTAtOTgxZS01YTBjMTNkNjAxZGYiLCJ4LWhhc3VyYS1lbXBsb3llZS1sZXZlbCI6MTB9fQ.8v1amuQGqQGx4Vy5UqdzHuqlTsIGiGb5o0y2jNe62Ms",
    "accept": "application/json"
}

# Prepare the form data (not JSON)
data = {
    "firstname": "John",
    "lastname": "Doe",
    "phone_number": "123456789",
    "id_number": "AB123456",
    "host_department": "e5ed40a0-94da-45c6-9a24-0013e20320e4",
    "visitor": "f319a7c3-90c1-480e-b525-8d2cb01e35dd",
    "status": "PENDING",
    "reason": "Meeting",
    "reg_no": "123ABC"
}

# Open the image file
files = {
    "face": open("/Users/ntchindagiscard/Downloads/WhatsApp Image 2024-10-10 at 20.35.50.jpeg", "rb")
}

# Send the request
response = requests.post(
    url,
    headers=headers,
    data=data,  # Send form data
    files=files  # Send the file separately
)

# Check the response
if response.status_code == 200:
    print("Success:", response.json())
else:
    print("Failed:", response.status_code, response.text)