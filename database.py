import asyncpg

import config


async def create_pool():
    return await asyncpg.create_pool(
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        host=config.DB_HOST,
        port=config.DB_PORT
    )


async def add_user(conn, user_id, first_name, last_name, email, registration_date):
    await conn.execute('''
    INSERT INTO users (user_id, first_name, last_name, email, registration_date) VALUES ($1, $2, $3, $4, $5)
    ''', user_id, first_name, last_name, email, registration_date)


async def get_user(conn, user_id):
    return await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)


async def get_all_users(conn):
    return await conn.fetch('SELECT * FROM users')
