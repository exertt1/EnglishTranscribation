from environs import Env
from pydantic import ConfigDict

class Config(ConfigDict):
    database_url: str
    secret_key: str
    refresh_secret_key: str
    debug: bool
    mode: str

def loading():
    env = Env()
    env.read_env()

    return Config(
        database_url=env("DATABASE_URL"),
        secret_key=env("SECRET_KEY"),
        refresh_secret_key=env("SECRET_REFRESH_KEY"),
        debug=env("DEBUG"),
        mode=env("MODE")
    )