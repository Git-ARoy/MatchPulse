FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
WORKDIR /app

# The package source must be present when setuptools builds the distribution.
COPY . .
RUN pip install --no-cache-dir .
RUN useradd --create-home --uid 10001 matchpulse && chown -R matchpulse:matchpulse /app
USER matchpulse

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
