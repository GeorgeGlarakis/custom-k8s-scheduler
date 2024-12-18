FROM python:3-alpine

WORKDIR /data_lists

COPY ./init_data.py .
COPY ./requirements.txt .

RUN apk add build-base libpq libpq-dev
RUN pip3 install -r requirements.txt

CMD python3 init_data.py