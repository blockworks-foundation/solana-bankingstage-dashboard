FROM python:3.9-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 8080

# CAUTION: gunicorn must not spawn multiple workers, otherwise the db connection pool will not limit the number of connections correctly
CMD \
 echo "$PGCACERT" | base64 --decode > ca.cer && echo "$PGCLIENTCERT" | base64 --decode > client.cer && echo "$PGCLIENTKEY" | base64 --decode > client-key.cer && \
 gunicorn app:webapp --workers 1 --threads 30 --bind 0.0.0.0:8080
