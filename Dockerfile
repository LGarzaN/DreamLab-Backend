FROM python:3.11

# Check Ubuntu version
RUN if ! [[ "18.04 20.04 22.04 23.04" == *"$(lsb_release -rs)"* ]]; then \
    echo "Ubuntu $(lsb_release -rs) is not currently supported."; \
    exit 1; \
fi

# Add Microsoft repository
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Update package lists and install msodbcsql18 and mssql-tools18
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 && \
    ACCEPT_EULA=Y apt-get install -y mssql-tools18 && \
    apt-get install -y unixodbc-dev

# Set PATH environment variable
ENV PATH="$PATH:/opt/mssql-tools18/bin"

WORKDIR /code

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY . .

EXPOSE 3100

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3100"]