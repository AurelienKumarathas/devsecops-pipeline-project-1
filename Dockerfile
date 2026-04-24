# Vulnerable Dockerfile - For Educational Purposes Only
# This file contains intentional security misconfigurations to validate
# container scanning gates. See Dockerfile.hardened on the hardened branch
# for the remediated version of every finding below.

# Vulnerability 1: Mutable base image tag - no digest pin
# python:3.9 is a version tag, not 'latest', but version tags are mutable.
# The Python Docker team can silently update what python:3.9 points to.
# A compromised upstream update becomes part of your build without any
# source code change. Fix: pin to a specific SHA digest.
FROM python:3.9

# Vulnerability 2: Container runs as root
# No USER instruction means the application process runs as UID 0.
# Any RCE vulnerability immediately grants root inside the container,
# significantly lowering the bar for host escape. CIS Docker Benchmark 4.1.
# Fix: create a dedicated low-privilege user and add USER before CMD.

# Vulnerability 3: Unnecessary packages installed
# curl, wget, vim, and net-tools serve no runtime purpose for this application.
# Post-exploitation, each is a useful attacker tool:
#   curl/wget  -> payload download
#   net-tools  -> network reconnaissance (ifconfig, netstat, route)
#   vim        -> GTFObin for shell escape and privilege escalation
# Fix: use python:3.9-slim and install only runtime dependencies.
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    vim \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

EXPOSE 5000

# Vulnerability 4: No HEALTHCHECK instruction
# Without HEALTHCHECK, Docker and container orchestrators (ECS, Kubernetes)
# cannot detect whether the application is alive and serving requests.
# A process that has crashed or deadlocked continues to receive traffic
# with no automated recovery or restart. CIS Docker Benchmark 4.6.
# Fix: HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:5000/health || exit 1

# Vulnerability 5: Shell form CMD
# CMD python src/vulnerable_app.py spawns /bin/sh -c as a wrapper.
# docker stop sends SIGTERM to the shell, not to Python. The Python process
# never receives a graceful shutdown signal and is force-killed after the
# stop timeout, dropping in-flight requests and open DB connections.
# Fix: exec form CMD ["python", "src/vulnerable_app.py"]
CMD python src/vulnerable_app.py
