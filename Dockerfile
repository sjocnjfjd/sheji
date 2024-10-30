FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8000

# 修改启动命令
CMD gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:$PORT --timeout 120 app:app