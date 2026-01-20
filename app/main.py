import secrets
import sqlite3
import datetime

import jwt
from click.testing import make_input_stream
from dns.opcode import QUERY
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from passlib.utils.des import mdes_encrypt_int_block

from .security import get_user_from_db, append_db, append_token
from .config import loading
from .security import create_jwt_token, create_refresh_token, get_user_from_access_token, pwd_contxt, get_user_from_refresh_token
from .models import User, UserInDB
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from .logger import logger
from typing import Annotated, final
from .enums import *
import asyncpg
# from app.database.db import get_database
from contextlib import asynccontextmanager

from app.models import Item, User, ToDo

limiter = Limiter(key_func=get_remote_address)
config = loading()
# pool: asyncpg.Pool | None = None

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global pool
#     pool = await asyncpg.create_pool(
#         dsn=config.get("database_url"),
#         min_size=5,
#         max_size=20
#     )
#     print("pool created")
#
#     yield
#
#     await pool.close()

security = HTTPBasic()

app = FastAPI()
app.add_middleware(SlowAPIMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)



def authenticate(user_log: User = Depends(security)):
    err = SUCCESS
    user: UserInDB = get_user_from_db(user_log.username)
    logger.info(type(user))
    if user:
        if pwd_contxt.verify(user_log.password, user.hashed_password):
            return user, err
        err = COMPARE_FAILED_ERROR
        return user, err
    err = NOT_FOUND_ERROR
    return None, err

@app.get("/login")
@limiter.limit("5/minute")
async def login(request: Request, user_and_err: tuple[UserInDB | None, int] = Depends(authenticate)):
    user = user_and_err[0]
    err = user_and_err[1]
    if err == COMPARE_FAILED_ERROR:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"detail": "Authorization failed"})

    if user and err == SUCCESS:
        data = {"sub": user.username}
        access_token: str = create_jwt_token(data)
        refresh_token: str = create_refresh_token(data)
        append_token(refresh_token)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "User not found"})

@app.post("/refresh")
@limiter.limit("5/minute")
async def refresh(request: Request, user_and_result: tuple[UserInDB | None, int] = Depends(get_user_from_refresh_token)):
    user, err = user_and_result
    if err == NOT_FOUND_ERROR:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"detail": "Token not is exist"})
    if err == EXPIRED_ERROR:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    data = {"sub": user.username}

    refresh_token = create_refresh_token(data)
    access_token = create_jwt_token(data)
    append_token(refresh_token)
    return {
        "refresh_token": refresh_token,
        "access_token": access_token
    }

@app.get("/protected_resource")
async def protected_resource(username: str = Depends(get_user_from_access_token)):
    if username:
        return {"msg": f"Hello {username}"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"detail": "Authorization Failed"})

# @app.post("/register")
# async def add_user(user: User):
#     db: sqlite3.Connection = get_db_connection()
#     cursor = db.cursor()
#     cursor.execute('''
#         INSERT INTO users (username, password)
#         VALUES (?, ?);
#     ''', (user.username, user.password))
#     db.commit()
#     db.close()
#     return {"msg": "User successfully added"}
#
# @app.get("/check_users")
# async def check():
#     db: sqlite3.Connection = get_db_connection()
#     cursor = db.cursor()
#     cursor.execute('''
#         SELECT username, password FROM users;
#     ''')
#     result = cursor.fetchall()
#     db.close()
#     return {
#         "users": result
#     }
# @app.post("/add_item")
# async def create_item(item: Item, db: asyncpg.Connection = Depends(get_db_connection)):
#     await db.execute('''
#     INSERT INTO items (name)
#     VALUES ($1)
#     ''', item.name)
#     return {"msg": f"item {item.name} successfully added"}
#
# @app.post("/add_todo")
# async def add_todo(todo: ToDo, db: asyncpg.Connection = Depends(get_db_connection)):
#     await db.execute('''
#         insert into todo (
#             title,
#             description
#         )
#         values ($1, $2)
#     ''',todo.title, todo.description)
#     await db.close()
#
#     return {"msg": "todo successfully added!"}
#
# @app.get("/get_todo/{id}")
# async def get_todos(id: int, db: asyncpg.Connection = Depends(get_db_connection)):
#     result = await db.fetchrow('''
#         SELECT * FROM todo
#         WHERE id = $1
#     ''', id)
#     await db.close()
#     return {"result": result}
#
# @app.put("/update_todo/{id}")
# async def update_todo(id: int, payload: dict, db: asyncpg.Connection = Depends(get_db_connection)):
#
#     await db.execute('''
#         update todo
#         set
#             title = $1,
#             description = $2,
#             completed = $3
#         where id = $4
#     ''', payload["title"], payload["description"], payload["completed"], id)
#     await db.close()
#     return {"msg": "todo is successfully is updated"}
#
# @app.delete("/delete_todo/{id}")
# async def delete_todo(id: int, db: asyncpg.Connection = Depends(get_db_connection)):
#     await db.execute('''
#         DELETE FROM todo
#         WHERE id = $1
#     ''', id)
#     await db.close()
#     return "msg: todo is successfully deleted"
#
# @app.delete("/users/{id}")
# async def delete_user(id: int, db: asyncpg.Connection = Depends(get_db_connection)):
#     await db.execute('''
#         DELETE FROM users
#         WHERE id = $1
#     ''', id)
#     await db.close()
#     return {"msg": "user is successfully deleted"}
#
# @app.post("/user_add")
# async def add_user(user: User, db: asyncpg.Connection = Depends(get_db_connection)):
#     await db.execute('''
#         INSERT INTO users (username, password)
#         VALUES ($1, $2)
#     ''', user.username, user.password)
#
#     await db.close()
#
#     return {"msg": f"user {user.username} is successfully added"}

@app.get("/todos")
async def get_todos(
    limit: int | None = None,
    offset: int = 0,
    sort_by: str  | None = None,
    completed: bool | None = None,
    created_after: datetime.datetime | None = None,
    created_before: str | None = None,
    title_contains: str | None = None
):
    db = await asyncpg.connect(config.get("database_url"))

    query_parts = ["SELECT * FROM todo"]
    params_part = []
    conditions = []
    if completed is not None:
        conditions.append(f"completed = ${len(params_part) + 1}")
        params_part.append(completed)

    if created_after:
        conditions.append(f"creation_time > ${len(params_part) + 1}")
        params_part.append(created_after)

    if created_before:
        conditions.append(f"creation_time < ${len(params_part) + 1}")
        params_part.append(created_before)

    if title_contains:
        conditions.append(f"""title ILIKE ${len(params_part) + 1}""")
        params_part.append(f"%{title_contains}%")

    if conditions:
        query_parts.append("WHERE " + " AND ".join(conditions))

    if sort_by:
        minus = False
        if sort_by[0] == '-':
            sort_by = sort_by[1:]
            minus = True
        query_parts.append(f"ORDER BY ${len(params_part) + 1}" + " DESC" if minus else "")
        params_part.append(sort_by)

    if limit:
        query_parts.append(f"LIMIT ${len(params_part) + 1}")
        params_part.append(limit)

    if offset:
        query_parts.append(f"OFFSET ${len(params_part) + 1}")
        params_part.append(offset)

    final_query = " ".join(query_parts)
    print(final_query)
    print(title_contains)
    result = await db.fetch(final_query, *params_part)
    await db.close()
    return {"result": result}

