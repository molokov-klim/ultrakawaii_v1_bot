import asyncpg


async def create_pool():
    return await asyncpg.create_pool(
        user='your_user_name',
        password='your_password',
        database='your_database_name',
        host='your_host',
        port='your_port'
    )


