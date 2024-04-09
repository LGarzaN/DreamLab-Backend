FROM python:3.11

# Install ODBC Driver 17 for SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY app/ /code/app/

EXPOSE 3100

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3100"]
