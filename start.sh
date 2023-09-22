#!/bin/sh

# checks if database is available now, if not - wait 1 second
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

# run migrations and start the server
python manage.py migrate
python manage.py runserver 0.0.0.0:8000