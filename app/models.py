from pydantic import BaseModel, field_validator, BaseConfig

from passlib.context import CryptContext

ctx = CryptContext(schemes=["bcrypt"])

class Item(BaseModel):
    name: str

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

    @field_validator("hashed_password")
    @classmethod
    def hashing(cls, v):
        if isinstance(v, str):
            return ctx.hash(v)
        raise ValueError("Is not needed type")

class ToDo(BaseModel):
    id: int
    title: str
    description: str
    completed: bool