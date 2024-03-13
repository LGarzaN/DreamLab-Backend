FROM python:3.11

# Install necessary packages for ODBC
RUN apt-get update && apt-get install -y curl apt-transport-https gnupg2

# Add Microsoft's repository for ODBC driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/18.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Install ODBC driver and unixODBC
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# Configure the ODBC driver
RUN echo "[ODBC Driver 17 for SQL Server]\n\
 Description=Microsoft ODBC Driver 17 for SQL Server\n\
 Driver=/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.5.so.2.1\n\
 UsageCount=1" >> /etc/odbcinst.ini

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

EXPOSE 3100

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3100"]