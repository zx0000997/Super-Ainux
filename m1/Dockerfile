FROM docker.io/library/python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SAS_M1_DATABASE_URL=sqlite:////data/sas_m1.db

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY sas_m1 ./sas_m1

RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 8080
CMD ["uvicorn", "sas_m1.main:app", "--host", "0.0.0.0", "--port", "8080"]
