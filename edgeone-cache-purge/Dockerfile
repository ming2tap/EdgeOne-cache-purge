FROM python:3.11-slim

WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 升级 pip 并安装依赖（所有依赖都是纯 Python 包，无需编译工具）
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY . .

# 创建数据目录
RUN mkdir -p /app/data && chmod 755 /app/data

# 暴露端口
EXPOSE 5000

# 运行应用
CMD ["python", "app.py"]
