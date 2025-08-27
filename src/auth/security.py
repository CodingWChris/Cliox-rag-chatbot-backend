from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..config.settings import settings

# API Key authentication
security = HTTPBearer(auto_error=False)

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key for production usage"""
    if settings.environment == "production" and settings.api_key:
        if not credentials or credentials.credentials != settings.api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False, 
                    "error": "invalid_api_key",
                    "message": "Invalid or missing API key"
                }
            )
    return credentials

async def optional_verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional API key verification - for endpoints that can work with or without auth"""
    if settings.api_key and credentials:
        if credentials.credentials != settings.api_key:
            raise HTTPException(
                status_code=401,
                detail={
                    "success": False, 
                    "error": "invalid_api_key",
                    "message": "Invalid API key provided"
                }
            )
    return credentials
