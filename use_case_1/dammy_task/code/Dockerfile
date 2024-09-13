FROM python:3

WORKDIR /code_pod

COPY ./code.py .
COPY ./requirements.txt .

RUN apt-get update
RUN pip3 install -r requirements.txt

CMD python3 code.py