"""
Database Infrastructure Layer для Webhook Dispatcher.

Содержит Repository паттерн и инфраструктурный код для работы с SQLite.
Следует принципам Clean Architecture - изолирует доменные модели от деталей БД.
"""

import os
from pathlib import Path
from typing import AsyncGenerator, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func
from contextlib import asynccontextmanager
import logging

from .models import Base, WebhookLogModel

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """
    Конфигурация базы данных.
    
    Использует pathlib для кроссплатформенных путей и обеспечивает
    правильное расположение БД относительно корня проекта.
    """
    
    def __init__(self):
        # Определяем корень проекта (папка выше app/)
        self.project_root = Path(__file__).parent.parent
        
        # Папка для данных
        self.data_dir = self.project_root / "data"
        
        # Создаем папку если не существует
        self.data_dir.mkdir(exist_ok=True)
        
        # Абсолютный путь к файлу БД
        self.db_path = self.data_dir / "webhook_audit.db"
        
        # URL для SQLAlchemy с абсолютным путем
        self.database_url = f"sqlite+aiosqlite:///{self.db_path.absolute()}"
        
        logger.info(f"📁 Database path: {self.db_path.absolute()}")
        logger.info(f"🔗 Database URL: {self.database_url}")


class DatabaseRepository:
    """
    Repository для работы с вебхук логами.
    
    Инкапсулирует все операции с базой данных и предоставляет
    чистый интерфейс для доменного слоя.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def save_webhook_log(self, webhook_log: WebhookLogModel) -> WebhookLogModel:
        """
        Сохраняет запись вебхука в базу данных.
        
        Args:
            webhook_log: Модель для сохранения
            
        Returns:
            WebhookLogModel: Сохраненная модель
        """
        self.session.add(webhook_log)
        await self.session.commit()
        await self.session.refresh(webhook_log)
        return webhook_log
    
    async def get_webhook_log(self, webhook_id: str) -> Optional[WebhookLogModel]:
        """
        Получает запись вебхука по ID.
        
        Args:
            webhook_id: Уникальный идентификатор
            
        Returns:
            Optional[WebhookLogModel]: Модель или None
        """
        result = await self.session.execute(
            select(WebhookLogModel).where(WebhookLogModel.id == webhook_id)
        )
        return result.scalar_one_or_none()
    
    async def get_webhooks_by_status(self, status: str, limit: int = 100) -> List[WebhookLogModel]:
        """
        Получает вебхуки по статусу.
        
        Args:
            status: Статус для фильтрации
            limit: Максимальное количество записей
            
        Returns:
            List[WebhookLogModel]: Список моделей
        """
        result = await self.session.execute(
            select(WebhookLogModel)
            .where(WebhookLogModel.status == status)
            .order_by(WebhookLogModel.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Получает статистику по вебхукам.
        
        Returns:
            Dict[str, Any]: Словарь со статистикой
        """
        # Общее количество
        total_result = await self.session.execute(select(func.count(WebhookLogModel.id)))
        total_webhooks = total_result.scalar()
        
        # По статусам
        status_result = await self.session.execute(
            select(WebhookLogModel.status, func.count(WebhookLogModel.id))
            .group_by(WebhookLogModel.status)
        )
        status_breakdown = dict(status_result.all())
        
        # По типам событий
        event_result = await self.session.execute(
            select(WebhookLogModel.event_type, func.count(WebhookLogModel.id))
            .group_by(WebhookLogModel.event_type)
        )
        event_breakdown = dict(event_result.all())
        
        return {
            "total_webhooks": total_webhooks,
            "status_breakdown": status_breakdown,
            "event_type_breakdown": event_breakdown
        }


class DatabaseManager:
    """
    Менеджер базы данных.
    
    Управляет жизненным циклом соединения с БД и предоставляет
    фабрики для создания сессий и репозиториев.
    """
    
    def __init__(self):
        self.config = DatabaseConfig()
        
        # Создание асинхронного движка
        self.engine = create_async_engine(
            self.config.database_url,
            echo=False,  # Установить в True для отладки SQL
            future=True,
            # Настройки для SQLite
            connect_args={"check_same_thread": False}
        )
        
        # Фабрика сессий
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def init_database(self) -> None:
        """
        Инициализирует базу данных и создает все таблицы.
        """
        try:
            logger.info("🔄 Инициализация базы данных...")
            
            async with self.engine.begin() as conn:
                # Создание всех таблиц
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("✅ База данных успешно инициализирована")
            logger.info(f"📁 Файл БД: {self.config.db_path.absolute()}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
    
    async def close(self) -> None:
        """
        Закрывает соединение с базой данных.
        """
        try:
            logger.info("🔄 Закрытие соединения с базой данных...")
            await self.engine.dispose()
            logger.info("✅ Соединение закрыто")
        except Exception as e:
            logger.error(f"❌ Ошибка закрытия базы данных: {e}")
    
    async def health_check(self) -> bool:
        """
        Проверка здоровья соединения с базой данных.
        
        Returns:
            bool: True если соединение работает
        """
        try:
            async with self.session_factory() as session:
                result = await session.execute(select(1))
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"❌ Проблема с БД: {e}")
            return False
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager для получения сессии БД.
        
        Yields:
            AsyncSession: Асинхронная сессия SQLAlchemy
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    def get_repository(self, session: AsyncSession) -> DatabaseRepository:
        """
        Создает экземпляр репозитория для работы с данными.
        
        Args:
            session: Активная сессия БД
            
        Returns:
            DatabaseRepository: Репозиторий для операций с БД
        """
        return DatabaseRepository(session)


# Глобальный экземпляр менеджера БД
database_manager = DatabaseManager()


# FastAPI dependencies
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency для получения сессии БД.
    
    Yields:
        AsyncSession: Асинхронная сессия для операций с БД
    """
    async with database_manager.get_session() as session:
        yield session


async def get_repository(session: AsyncSession = None) -> DatabaseRepository:
    """
    FastAPI dependency для получения репозитория.
    
    Args:
        session: Сессия БД (инжектируется автоматически)
        
    Returns:
        DatabaseRepository: Репозиторий для операций
    """
    if session is None:
        raise ValueError("Session is required")
    return database_manager.get_repository(session)


# Функции для обратной совместимости и удобства
async def init_database() -> None:
    """Инициализирует базу данных."""
    await database_manager.init_database()


async def close_database() -> None:
    """Закрывает соединение с базой данных."""
    await database_manager.close()


async def check_database_health() -> bool:
    """Проверяет здоровье базы данных."""
    return await database_manager.health_check()