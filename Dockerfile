FROM python:3.6


RUN apt-get update && \
    apt-get install -y \
	supervisor &&\
	rm -rf /var/lib/apt/lists/*

COPY supervisor-app.conf /etc/supervisor/conf.d/
COPY . /code/
WORKDIR /code

RUN pip3 install -r requirements.txt

ENV REDIS_HOST="10.10.10.32" \
    PG_DATABASE="hy" \
    PG_USER="hy" \
    PG_PASSWORD="hy" \
    PG_HOST="10.10.10.32" \
    PG_PORT="5432" \
    STATIC_FILE_URL="http://10.10.10.32:8000/"

EXPOSE 8080

CMD ["supervisord", "-n"]