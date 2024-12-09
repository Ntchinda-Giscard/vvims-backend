FROM python:3.9

# Switch to root user to install dependencies
USER root

# Step 1: Create the user
RUN adduser --disabled-password --gecos "" myuser

# Step 2: Create the /uploads directory
RUN mkdir /uploads

# Step 3: Change the ownership of the /uploads directory
RUN chown -R myuser:myuser /uploads

# Step 4: Set the user to myuser for running the app
USER myuser
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