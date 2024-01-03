# Base image
FROM python:3.8

# Set the working directory to /app
WORKDIR /app

# Copy necessary files into the container
COPY . .

# Install required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the FastAPI application by default
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
