# 官方 uv + Python 3.12 基础镜像
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 先只拷贝依赖文件，加快缓存命中
COPY pyproject.toml uv.lock ./

# 根据 uv.lock 安装依赖（只装运行时依赖）
RUN uv sync --frozen --no-dev

# 再拷贝项目代码
COPY . .

# 使用项目虚拟环境中的 Python/包
ENV PATH="/app/.venv/bin:${PATH}"

# 暴露 FastAPI 端口
EXPOSE 8080

# 默认启动 FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]