FROM python:3.12-alpine

WORKDIR /app

RUN apk update && apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    libffi-dev

COPY  requirements.txt .
RUN pip install -r requirements.txt

COPY . .


CMD ["python", "-m", "gunicorn", "backend.asgi:application", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000" ]

