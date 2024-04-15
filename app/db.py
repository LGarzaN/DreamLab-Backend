import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

class DB:
    def __init__(self):
        self.connection = None

    async def __aenter__(self):
        if self.connection is None or await self.is_closed():
            self.connection = self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.connection is not None and not await self.is_closed():
            self.connection.close()

    def connect(self):
        connection_string = os.getenv("AZURE_SQL_CONNECTIONSTRING")
        return pyodbc.connect(connection_string)

    async def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return None
        
    async def execute_query_insert(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
            return cursor.rowcount
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return None
    
    async def is_closed(self):
        if self.connection is None:
            return True
        try:
            return self.connection.closed
        except pyodbc.ProgrammingError:  # Handle case where connection is not open yet
            return True