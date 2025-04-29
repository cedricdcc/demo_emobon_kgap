# Backend Dockerfile
FROM python:3.9-slim

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application code
COPY ./ /app

# Set the working directory
WORKDIR /app

# Set entry point
ENTRYPOINT ["python"]

CMD ["server.py"]