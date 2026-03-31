
from fastapi import HTTPException
from app.core.config import settings
from fastapi import Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="Auth-Token", auto_error=True)

async def get_auth_token(auth_token: str = Security(api_key_header)) -> str:
  if(auth_token != settings.AUTH_TOKEN):
    raise HTTPException(status_code=401, detail="Invalid authentication token")
  return auth_token 