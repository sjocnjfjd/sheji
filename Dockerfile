FROM python:3.9-slim

WORKDIR /app

# 更新 pip
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8000

CMD gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app