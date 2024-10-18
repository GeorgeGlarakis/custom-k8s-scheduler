FROM python:3-alpine

WORKDIR /code_pod

COPY ./code.py .
COPY ./requirements.txt .

RUN pip3 install -r requirements.txt

CMD python3 code.py