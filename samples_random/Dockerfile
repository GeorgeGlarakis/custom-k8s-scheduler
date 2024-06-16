FROM python:3
WORKDIR /scheduler
COPY ./sample_rand.py .
RUN apt-get update
RUN pip3 install kubernetes
CMD python3 sample_rand.py