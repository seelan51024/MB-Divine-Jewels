FROM python:3.11-slim

RUN apt-get update && apt-get install -y gcc libffi-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir fastapi==0.110.0 uvicorn==0.29.0 PyJWT==2.8.0 bcrypt==4.1.2 pydantic==2.6.4 python-multipart==0.0.9

RUN mkdir -p database

EXPOSE 8000

CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
