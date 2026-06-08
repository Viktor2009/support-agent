FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN adduser --disabled-password --gecos "" appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY knowledge ./knowledge
COPY widget ./widget
COPY admin ./admin
COPY scripts/docker-entrypoint.sh ./scripts/docker-entrypoint.sh

RUN chmod +x scripts/docker-entrypoint.sh && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENTRYPOINT ["scripts/docker-entrypoint.sh"]
