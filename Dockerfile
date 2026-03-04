# Vulnerable Dockerfile - For Educational Purposes
# Contains intentional security misconfigurations

# Vulnerability 1: Using latest tag (unpredictable)
FROM python:3.9

# Vulnerability 2: Running as root (no USER instruction)

# Vulnerability 3: Installing unnecessary packages
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    vim \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Vulnerability 4: Exposing port
EXPOSE 5000

# Vulnerability 5: Using shell form (not exec form)
CMD python src/vulnerable_app.py
