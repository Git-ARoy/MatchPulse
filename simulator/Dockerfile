FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV SIMULATOR_PORT=8050
ENV MATCHPULSE_API_URL=http://backend:8000

EXPOSE 8050

CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8050"]
