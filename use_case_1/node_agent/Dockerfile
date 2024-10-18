FROM python:3-alpine

WORKDIR /node_agent

COPY ./node_code.py .
COPY ./requirements.txt .

RUN pip3 install -r requirements.txt

CMD python3 node_code.py