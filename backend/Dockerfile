# ============================================================
# CareerAI 后端镜像（FastAPI + Uvicorn）
# ============================================================
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

# 国内服务器构建可通过 --build-arg PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple 加速
ARG PIP_INDEX_URL=https://pypi.org/simple

# asyncpg/cryptography 等在部分环境下需要编译依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

# 先装依赖，利用 Docker 层缓存
COPY requirements.txt .
RUN pip install --index-url ${PIP_INDEX_URL} -r requirements.txt

# 拷贝业务代码
COPY . .

RUN mkdir -p /app/uploads

EXPOSE 8000

# 容器内健康检查（用标准库，无需安装 curl）
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
