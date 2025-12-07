# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Download nltk data
# Include NLTK punkt and punkt_tab to allow sentence tokenization
RUN python -m nltk.downloader punkt punkt_tab

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 5050 available to the world outside this container
EXPOSE 5050

# Define environment variable
ENV NAME Vectorstore

# Run the Flask app with multiple workers using Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5050", "main:app"]