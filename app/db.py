from .models import UserInDB
from .config import loading, Config

config: Config = loading()

DATA = [
    UserInDB(**{"username": "admin", "hashed_password": "adminpass"})
]

TOKENS_DB = []

