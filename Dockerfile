FROM python:3.13-alpine3.20

ENV PYTHONUNBUFFERED=1
ENV PYTHONUNDONTWRITEBYTECODE=1
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000
RUN python manage.py migrate
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "backend.wsgi"]
