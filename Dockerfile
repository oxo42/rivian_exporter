FROM python:3.11-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1
# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

RUN pip3 install poetry

WORKDIR /app
COPY . /app
RUN poetry config virtualenvs.create false
RUN poetry install --only main

RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "rivian_exporter"]
CMD ["prometheus"]