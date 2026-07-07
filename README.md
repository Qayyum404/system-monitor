# System Monitor API

A lightweight containerized API that exposes real-time system metrics (CPU, memory, disk) built with FastAPI and Docker. Designed as a DevOps learning project demonstrating containerization and CI/CD practices.

## What It Does

Hit the /metrics endpoint and get back live system stats:
- CPU usage percentage
- Memory total, used, free, and usage percentage
- Disk total, used, free, and usage percentage

## Tech Stack

- FastAPI - Python web framework
- psutil - system metrics library
- Docker - containerization
- GitHub Actions - CI/CD pipeline

## Example Response

GET /metrics returns:
{
  "cpu": {"usage_percent": 0.5},
  "memory": {"total_gb": 7.6, "used_gb": 1.12, "free_gb": 6.48, "usage_percent": 14.7},
  "disk": {"total_gb": 1006.85, "used_gb": 3.63, "free_gb": 952.01, "usage_percent": 0.4}
}

## Running Locally with Docker

1. Clone the repo:
git clone https://github.com/Qayyum404/system-monitor.git
cd system-monitor

2. Build and run:
docker build -t system-monitor .
docker run -d -p 8000:8000 system-monitor

3. Test:
curl http://localhost:8000/metrics

4. Open interactive docs:
http://localhost:8000/docs

## CI/CD

Every push to main automatically builds the Docker image and runs smoke tests against both endpoints via GitHub Actions.
