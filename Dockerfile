FROM python:3.9-slim-buster

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 8080
CMD \
 echo "$PGCACERT" | base64 --decode > ca.cer && echo "$PGCLIENTCERT" | base64 --decode > client.cer && echo "$PGCLIENTKEY" | base64 --decode > client-key.cer && \
 flask run --host 0.0.0.0 --port 5050
