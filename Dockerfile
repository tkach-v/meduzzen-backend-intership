FROM python:3.9-alpine
LABEL maintainer="https://github.com/tkach-v"

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

COPY . /app
WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r ./requirements.txt

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]