FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY services ./services
RUN pip install --no-cache-dir .
COPY knowledge_base ./knowledge_base
COPY data ./data
COPY scripts ./scripts
RUN mkdir -p /app/runtime
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn services.agent_api.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
