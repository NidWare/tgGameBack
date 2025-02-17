FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

WORKDIR /app

COPY ./app /app
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
