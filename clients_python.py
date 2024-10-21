import pyqrcode
import uuid
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from io import BytesIO
import os

# Generate a UUID
unique_id = "6a7b670b-a5be-45b9-a74b-f9544482320f"

# Generate the QR code using the UUID
url = pyqrcode.QRCode(unique_id, error='H')

# Save the QR code into a BytesIO object (in memory)
buffer = BytesIO()
url.png(buffer, scale=10)  # Generate the QR code without extra quiet zone
buffer.seek(0)

# Open the QR code image
qr_image = Image.open(buffer).convert("RGBA")

# Open the logo image using the specified path
logo_path = '/Users/ntchindagiscard/Downloads/PHOTO-2024-10-20-16-09-38.jpg'
if not os.path.exists(logo_path):
    raise FileNotFoundError(f"Logo file not found at {logo_path}")

try:
    logo = Image.open(logo_path).convert("RGBA")  # Ensure logo is RGBA
    print(f"Logo size: {logo.size}")  # Debugging statement to check logo size
except Exception as e:
    print(f"Error opening logo: {e}")
    raise

# Resize the logo to fit within the QR code
logo_size = (80, 80)  # Adjust the size based on the logo and QR code size
logo = logo.resize(logo_size)

# Add white padding around the logo
padding_size = 20  # Define padding size (white space) around the logo
logo_with_padding = Image.new('RGBA', (logo_size[0] + padding_size, logo_size[1] + padding_size), (255, 255, 255, 255))  # White background
logo_with_padding.paste(logo, (padding_size // 2, padding_size // 2))  # Paste the logo with padding without a mask

# Create a rounded rectangle mask for the padded logo (border radius of 15px)
radius = 15
mask = Image.new("L", (logo_with_padding.width, logo_with_padding.height), 0)  # Create a black mask
draw = ImageDraw.Draw(mask)
draw.rounded_rectangle([(0, 0), (logo_with_padding.width, logo_with_padding.height)], radius=radius, fill=255)  # Rounded corners with 15px radius

# Apply the rounded mask to the logo with padding (border radius of 15px)
logo_with_padding.putalpha(mask)  # Apply the mask for rounded corners

# Calculate the center position for the logo on the QR code
qr_width, qr_height = qr_image.size
logo_pos = ((qr_width - logo_with_padding.width) // 2, (qr_height - logo_with_padding.height) // 2)

# Create a new image for QR code with the logo
qr_with_logo = Image.new('RGBA', qr_image.size, (255, 255, 255, 255))  # White background for the QR code
qr_with_logo.paste(qr_image, (0, 0))  # Paste the QR code onto the white background

# Paste the logo onto the QR code in the center
qr_with_logo.paste(logo_with_padding, logo_pos, logo_with_padding)  # The third argument is the mask to keep transparency

# Save the QR code with logo and padding into another BytesIO object (no intermediate file)
qr_with_logo_buffer = BytesIO()
qr_with_logo.save(qr_with_logo_buffer, format="PNG")
qr_with_logo_buffer.seek(0)

# Create an ImageReader object from the BytesIO object
qr_image_for_pdf = ImageReader(qr_with_logo_buffer)

# Create a PDF file and insert the QR code with logo
pdf_filename = 'vvims-fodecc-annexe.pdf'
c = canvas.Canvas(pdf_filename, pagesize=A4)

# Set the dimensions and position for the image on the PDF (center it on the page)
width, height = A4
c.drawImage(qr_image_for_pdf, (width - 300) / 2, (height - 300) / 2, 300, 300)

# Save the PDF
c.showPage()
c.save()

print(f"QR code with UUID and logo saved as {pdf_filename}, UUID: {unique_id}")