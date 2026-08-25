FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY services ./services
COPY data ./data
RUN pip install --no-cache-dir .
RUN mkdir -p /app/runtime
EXPOSE 8001
CMD ["sh", "-c", "exec uvicorn services.mock_erp.app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
