FROM python:3.11.10

WORKDIR /app

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production

# Cài đặt các dependencies hệ thống
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục cho dữ liệu và logs
RUN mkdir -p /app/data /app/logs
VOLUME ["/app/data", "/app/logs"]

# Sao chép requirements trước để tận dụng cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng
COPY . .

# Tạo thư mục data nếu chưa tồn tại
RUN mkdir -p /app/data/research_tasks

# Thiết lập quyền truy cập
RUN chmod -R 755 /app

# Mở cổng cho ứng dụng
EXPOSE 8000

# Lệnh khởi động ứng dụng
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 