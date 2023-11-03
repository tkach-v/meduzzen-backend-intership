FROM python:3.11-alpine
LABEL maintainer="https://github.com/tkach-v"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir /app
WORKDIR /app

COPY ./requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r ./requirements.txt

COPY . /app/

RUN chmod +x ./start.sh

EXPOSE 8000