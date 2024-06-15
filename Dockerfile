FROM python:3.12-slim

WORKDIR /app

COPY ./requirements.txt /app

RUN pip install --upgrade pip && pip install -r /app/requirements.txt

COPY . /app

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
