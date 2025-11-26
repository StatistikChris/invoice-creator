# Use official Python runtime as base image yeah
FROM python:3.11-slim

# Install system dependencies including LaTeX
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Expose port
EXPOSE 8080

# Set environment variable for Cloud Run
ENV PORT=8080

# Run the application with gunicorn - single worker with threads to reduce memory usage
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 120 --worker-class sync app:app
