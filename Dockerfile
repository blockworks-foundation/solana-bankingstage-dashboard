FROM python:3.9-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 8080

CMD ["gunicorn", "app:webapp", "--bind", "0.0.0.0:8080"]
