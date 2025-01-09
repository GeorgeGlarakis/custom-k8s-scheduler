FROM python:3-alpine

WORKDIR /node_task_runner

COPY ./scripts/* .

RUN apk add build-base libpq libpq-dev
RUN pip3 install -r requirements.txt

CMD python3 task_runner.py