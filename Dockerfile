FROM spex.common:latest
USER root

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY ./microservices/ms-pipeline-manager /app/services/app
COPY ./common /app/common

WORKDIR /app/services/app

RUN pipenv install --system --deploy --ignore-pipfile

CMD ["python", "app.py"]
