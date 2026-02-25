# Use official Python runtime as a parent image
FROM python:3.12-slim

# Install system dependencies for OpenCV and Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create uploads folder
RUN mkdir -p /app/uploads

# Expose the port Flask runs on
EXPOSE 5001

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "main:app"]
