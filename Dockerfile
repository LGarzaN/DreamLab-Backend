FROM python:3.11

RUN apt-get update \
        && apt-get install -y --no-install-recommends build-essential gcc unixodbc-dev 

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

EXPOSE 3100

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3100"]