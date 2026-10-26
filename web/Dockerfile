FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 notesapp && useradd --uid 10001 --gid notesapp --no-create-home notesapp
COPY web/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY web/ ./
COPY tests/ ./tests/
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
EXPOSE 5000
CMD ["sh", "-c", "python migrate_comments.py && exec gunicorn --bind 0.0.0.0:5000 --workers 1 --threads 4 --timeout 30 --max-requests 1000 --max-requests-jitter 30 --access-logfile - --error-logfile - app:app"]
