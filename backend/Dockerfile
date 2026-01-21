FROM python:3.11-slim

WORKDIR /app

# Install git (required by GitPython)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY . .

# Render provides the port via PORT env var, but we default to 8000
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --proxy-headers --host 0.0.0.0 --port ${PORT}"]
