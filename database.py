import inspect

import asyncpg

import config



async def create_pool():
    
    try:
        return await asyncpg.create_pool(
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME,
            host=config.DB_HOST,
            port=config.DB_PORT
        )
    except Exception as error:
        pass


async def add_user(conn, user_id, first_name, last_name, email, registration_date):
    try:
        
        await conn.execute('''
        INSERT INTO users (user_id, first_name, last_name, email, registration_date) VALUES ($1, $2, $3, $4, $5)
        ''', user_id, first_name, last_name, email, registration_date)
    except Exception as error:
        pass


async def get_user(conn, user_id):
    try:
        
        return await conn.fetchrow('SELECT * FROM users WHERE user_id = $1', user_id)
    except Exception as error:
        pass


async def get_all_users(conn):
    try:
        
        return await conn.fetch('SELECT * FROM users')
    except Exception as error:
        pass
