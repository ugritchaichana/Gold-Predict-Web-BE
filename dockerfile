# # Dockerfile

# FROM python:3.12

# ENV PYTHONUNBUFFERED=1

# WORKDIR /app

# COPY requirements.txt /app/

# RUN pip install --upgrade pip && \
#     pip install -r requirements.txt

# COPY . /app/

# # Expose the port the app runs on
# EXPOSE 8000

# # Default command is to run the server
# CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


# Base Image
FROM python:3.12-slim

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
