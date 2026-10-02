FROM python:3.13.12
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

ENV PYTHONPATH=/app

# start cron in foreground and set it as executable command for when the container starts
CMD ["python", "-m", "code.etl_pipeline"]
