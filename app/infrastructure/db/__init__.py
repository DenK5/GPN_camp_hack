from app.infrastructure.db.base import Base, engine

async def init_db():
    # Используем асинхронный контекст для работы с движком
    async with engine.begin() as conn:
        # Запускаем создание всех таблиц через асинхронный метод
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    import asyncio
    asyncio.run(init_db())  # Асинхронный запуск функции
    print("Database initialized successfully")
