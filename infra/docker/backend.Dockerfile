FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PORT=10000
EXPOSE 10000
CMD gunicorn --bind "0.0.0.0:${PORT}" --workers 2 --timeout 60 "src.app:create_app()"
