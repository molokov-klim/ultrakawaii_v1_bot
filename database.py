import asyncpg


async def create_pool():
    return await asyncpg.create_pool(
        user='your_user_name',
        password='your_password',
        database='your_database_name',
        host='your_host',
        port='your_port'
    )


async def create_table(conn):
    await conn.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id serial PRIMARY KEY,
        user_id INTEGER,
        name VARCHAR(50),
        email VARCHAR(50)
    );
    ''')


async def add_user(conn, user_id, name, email):
    await conn.execute('''
    INSERT INTO users (user_id, name, email) VALUES ($1, $2, $3)
    ''', user_id, name, email)
