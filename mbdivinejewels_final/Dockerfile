FROM python:3.11-slim
FROM python:3.11-slim

WORKDIR /app

COPY mbdivinejewels_final/backend/ .

RUN pip install --no-cache-dir fastapi==0.110.0 uvicorn[standard]==0.29.0 PyJWT==2.8.0 bcrypt==4.1.2 pydantic==2.6.4 python-multipart==0.0.9 gunicorn==21.2.0

CMD gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}
