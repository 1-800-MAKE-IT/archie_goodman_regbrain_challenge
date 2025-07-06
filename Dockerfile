#NOTE - for speed purposes, this file was created with ChatGPT as it is boilerplate.
FROM python:3.10-slim

# Set up work directory
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code
COPY . .

# Default command
CMD [ "bash" ]
