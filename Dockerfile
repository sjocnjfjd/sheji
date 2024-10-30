FROM python:3.9-slim

WORKDIR /app

# 复制并安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制所有文件
COPY . .

# 设置环境变量
ENV PORT=8000

# 修改启动命令
ENTRYPOINT ["gunicorn"]
CMD ["--worker-class", "eventlet", "-w", "1", "-b", "0.0.0.0:8000", "app:app"]