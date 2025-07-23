FROM python:3.12-slim

WORKDIR /workspace

# Update system packages to fix security vulnerabilities
RUN apt-get update && apt-get upgrade -y && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./app/

RUN pip install -r ./app/requirements.txt

COPY . ./app/

ENV PYTHONPATH=/workspace

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]