# import asyncio
# from sqlite3 import Connection
# from app.models import User
#
# from app.database.db import get_database
# from databases import Database
# from app.config import loading
#
# config = loading()
#
# async def create_table():
#     database: Database = Database(config.get("database_url"))
#     await database.connect()
#     await database.execute('''
#         INSERT INTO todo (title, description, completed, user_id, creation_time) VALUES
# ('Купить продукты', 'Молоко, хлеб, яйца, фрукты', true, 4, '2024-01-15 09:30:00'),
# ('Записаться к врачу', 'Терапевт, следующая неделя', false, 2, '2024-01-16 14:20:00'),
# ('Подготовить отчет', 'Ежеквартальный отчет по продажам', true, 3, '2024-01-17 11:45:00'),
# ('Починить кран', 'В ванной комнате течет вода', false, 3, '2024-01-18 16:10:00'),
# ('Прочитать книгу', '"1984" Джорджа Оруэлла', true, 2, '2024-01-19 20:00:00'),
# ('Запланировать отпуск', 'Выбрать отель и купить билеты', false, 5, '2024-01-20 10:15:00');
#     ''')
#     await database.disconnect()
#
# asyncio.run(create_table())

import asyncpg
import asyncio
from app.config import loading

config = loading()


async def test_todo_basics():
    conn = await asyncpg.connect(config.get("database_url"))
    res = await conn.fetch("""
        SELECT * FROM todo
        where title like '%ead%'
    """)
    print(res)
    await conn.close()

asyncio.run(test_todo_basics())