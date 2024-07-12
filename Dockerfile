FROM tiangolo/uvicorn-gunicorn-fastapi:python3.9

COPY ./app/main.py /app/main.py
COPY ./app/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
