FROM python:3.9.2
USER root

ENV PYTHONDONTWRITEBYTECODE = 1
ENV PYTHONUNBUFFERED = 1

COPY ./common ./common

WORKDIR /app
COPY ./ms-pipeline-manager /app

RUN pip install pipenv && pipenv install --system --deploy --ignore-pipfile && pip install -e ./../common/

CMD ["python", "app.py"]
