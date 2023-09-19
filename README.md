# meduzzen-backend-intership

## Local Setup

If you want to set up and run project locally, follow these steps:

1. Clone the repository:
```
git clone <repository_url>
cd meduzzen-backend-intership
```

2. Build the Docker Image:
```
docker build -t image_name .
```

3. Run the Docker Container:
```
docker run -p 8000:8000 image_name
```

This will start the development server at http://localhost:8000/.

You should now be able to access the project in your web browser at http://localhost:8000/.

## Execution of tests

If you want to run tests for the project, run this command:

```
docker run --rm image_name sh -c "python manage.py test"
```

You will see the tests results after completing all the tests.