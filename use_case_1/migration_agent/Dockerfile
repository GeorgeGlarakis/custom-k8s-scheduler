FROM python:3-alpine

WORKDIR /migration_agent

RUN apk add --update redis

COPY ./scripts/* .

RUN pip3 install -r requirements.txt

CMD sh migration_code.sh