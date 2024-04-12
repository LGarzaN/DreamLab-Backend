import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

connection_string = os.getenv("AZURE_SQL_CONNECTIONSTRING")

class DB:
    def __init__(self):
        try:
            self.conn = pyodbc.connect(connection_string)
            self.cursor = self.conn.cursor()
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            self.conn = None

    async def execute_query(self, query, params=None):
        try:
            print(f"Executing query: {query}")
            if params:
                print(params)
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return None
        
    async def execute_query_insert(self, query, params=None):
        try:
            print(f"Executing query: {query}")
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.conn.commit()
            return self.cursor.rowcount
        except pyodbc.Error as e:
            print(f"Database error: {e}")
            return None

    def close(self):
        self.conn.close()