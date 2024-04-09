from app.models import User
from app.db import DB

async def login(user: User, db:DB):
    try: 
        query = "SELECT * FROM dbo.Users WHERE username = ? AND password = ?"
        params = (user.username, user.password)
        results = await db.execute_query(query, params)

        if len(results) > 0:
            return True
        else:
            return False
        
    except Exception as e:
        raise RuntimeError(str(e))