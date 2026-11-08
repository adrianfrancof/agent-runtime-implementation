FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 arp
USER arp
EXPOSE 8000
CMD ["uvicorn", "arp.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
