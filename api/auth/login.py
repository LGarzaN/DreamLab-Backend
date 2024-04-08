from models import User
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

connection_string = os.getenv("AZURE_SQL_CONNECTIONSTRING")

async def login(user: User):
    try: 
        conn = pyodbc.connect(connection_string) 
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM dbo.Users")
        columns = [column[0] for column in cursor.description]  # Get column names
        results = [dict(zip(columns, row)) for row in cursor.fetchall()] 

        conn.close()

        if results and results[0]["username"] == user.username and results[0]["password"] == user.password:
            return True
        else:
            return False
    except Exception as e:
        raise RuntimeError(str(e))