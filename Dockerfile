# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY . /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install LibreOffice for DOCX to PDF conversion
RUN apt-get update \
    && apt-get install -y libreoffice-core libreoffice-writer libreoffice-java-common fontconfig --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Add the custom font
COPY fonts/majalla.ttf /usr/share/fonts/truetype/majalla.ttf

# Rebuild font cache
RUN fc-cache -fv

# Copy the rest of the application code
COPY . /app

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
