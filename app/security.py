from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordBearer
import jwt
from fastapi import Depends
from passlib.context import CryptContext
import secrets
from typing import Dict
from .config import loading
from datetime import datetime, timedelta
from .db import TOKENS_DB, DATA
from .enums import EXPIRED_ERROR, INCORRECT_ERROR, NOT_FOUND_ERROR, SUCCESS
from .models import UserInDB

config = loading()
secret_key = config.get("secret_key")
secret_refresh_key = config.get("refresh_secret_key")
ALGORITM: str = "HS256"
ACCESS_TOKEN_EXPIRES_MINUTE = 1
REFRESH_TOKEN_EXPIRES_MINUTE = 3

pwd_contxt = CryptContext(
    schemes=["bcrypt"]
)

oauth2 = OAuth2PasswordBearer(tokenUrl="login", refreshUrl="refresh")
security = HTTPBasic()

def create_jwt_token(data: Dict):
    to_encode = data.copy()
    to_encode.update({"type": "access"})
    expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRES_MINUTE)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, ALGORITM)

def create_refresh_token(data: Dict):
    to_encode = data.copy()
    to_encode.update({"type": "refresh"})
    expire = datetime.now() + timedelta(minutes=REFRESH_TOKEN_EXPIRES_MINUTE)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_refresh_key, ALGORITM)

def get_user_from_access_token(token = Depends(oauth2)):
    try:
        payload = jwt.decode(token, secret_key, ALGORITM)
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_user_from_refresh_token(token: str = Depends(oauth2)):
    payload = jwt.decode(token, secret_refresh_key, ALGORITM)
    for t in TOKENS_DB:
        try:
            payload_t = jwt.decode(t, secret_refresh_key, ALGORITM)
            if payload["type"] == "refresh":
                if payload["sub"] == payload_t["sub"]:
                    user = get_user_from_db(payload["sub"])
                    TOKENS_DB.remove(token)
                    return user, SUCCESS
            raise Exception("not refresh token")
        except jwt.ExpiredSignatureError:
            return None, EXPIRED_ERROR
        except jwt.InvalidTokenError:
            return None, INCORRECT_ERROR
    return None, NOT_FOUND_ERROR

def get_user_from_db(username: str):
    for user in DATA:
        if secrets.compare_digest(user.username, username):
            return user
    return None

def append_db(credentials: HTTPBasicCredentials):
    DATA.append(UserInDB(**{"username": credentials.username, "hashed_password": credentials.password}))

def append_token(token: str):
    if token in TOKENS_DB:
        TOKENS_DB.remove(token)
    TOKENS_DB.append(token)