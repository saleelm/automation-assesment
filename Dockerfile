FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

WORKDIR /app

COPY pyproject.toml Makefile ./
COPY src/ ./src/
COPY tests/ ./tests/
COPY env/ ./env/
COPY conftest.py ./

RUN pip install --no-cache-dir -e ".[dev]"

ENV ENVIRONMENT=qa
ENV PLATFORM=web

CMD ["pytest", "--platform", "web"]
