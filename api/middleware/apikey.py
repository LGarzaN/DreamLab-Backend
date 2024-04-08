from fastapi import HTTPException, Header
import os

async def check_api_key(x_api_key: str = Header(None)):
    if os.getenv("API_KEY") == x_api_key:
        return True
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")