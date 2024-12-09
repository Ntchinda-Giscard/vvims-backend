FROM python:3.9

# Switch to root user to install dependencies
USER root

# Example to set user in Dockerfile
USER myuser
# Make the uploads directory writable by the user
RUN chown -R myuser:myuser /uploads
# Install necessary packages
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx && \
    rm -rf /var/lib/apt/lists/*
# Create a new user and switch to that user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /app

# Copy requirements file with proper ownership
COPY --chown=user ./requirements.txt requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code
COPY --chown=user . /app

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]