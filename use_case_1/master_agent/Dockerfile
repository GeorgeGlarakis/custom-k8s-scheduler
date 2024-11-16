FROM python:3-alpine

WORKDIR /master_agent

COPY ./scripts/* .

RUN pip3 install -r requirements.txt

CMD python3 master_code.py