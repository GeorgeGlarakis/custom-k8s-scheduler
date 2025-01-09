FROM python:3-alpine

WORKDIR /node_agent

COPY ./scripts/* .

RUN pip3 install -r requirements.txt

CMD python3 node_api.py