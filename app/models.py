"""
Domain Models для Webhook Dispatcher.

Содержит SQLAlchemy модели и доменные сущности для логирования входящих вебхуков.
Следует принципам Clean Architecture - модели не зависят от внешних сервисов.
"""

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Integer, DateTime, Index
from datetime import datetime
from typing import Optional
import uuid


class Base(DeclarativeBase):
    """
    Базовый класс для всех моделей SQLAlchemy.
    
    Следует принципам Domain-Driven Design.
    """
    pass


class WebhookLogModel(Base):
    """
    Доменная модель для логирования входящих вебхуков.
    
    Представляет агрегат в терминах DDD - полностью инкапсулирует
    логику работы с логами вебхуков и их жизненным циклом.
    """
    
    __tablename__ = "webhook_logs"

    # Primary Key - UUID для лучшей масштабируемости
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        doc="Уникальный идентификатор записи лога"
    )
    
    # Business Fields
    event_type: Mapped[str] = mapped_column(
        String(100), 
        index=True,
        doc="Тип события (lead.created, payment.succeeded, etc.)"
    )
    
    source: Mapped[str] = mapped_column(
        String(50),
        index=True,
        doc="Источник вебхука (tilda, robokassa, shopify, etc.)"
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        index=True,
        doc="Статус обработки: processing, success, error"
    )
    
    # Payload Storage - JSON в текстовом поле для гибкости
    payload: Mapped[str] = mapped_column(
        Text,
        doc="JSON данные вебхука (сырые или валидированные)"
    )
    
    # Error Handling
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, 
        nullable=True,
        doc="Детальное сообщение об ошибке обработки"
    )
    
    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow,
        index=True,
        doc="Время создания записи (UTC)"
    )
    
    # Составные индексы для производительности
    __table_args__ = (
        Index('idx_event_status', 'event_type', 'status'),
        Index('idx_source_created', 'source', 'created_at'),
        Index('idx_status_created', 'status', 'created_at'),
    )

    def __repr__(self) -> str:
        """Человекочитаемое представление модели."""
        id_short = self.id[:8] + "..." if self.id else "None"
        return (
            f"<WebhookLog("
            f"id={id_short}, "
            f"event_type={self.event_type}, "
            f"status={self.status}, "
            f"source={self.source}"
            f")>"
        )
    
    def to_dict(self) -> dict:
        """
        Преобразование модели в словарь для API ответов.
        
        Returns:
            dict: Словарь с данными модели
        """
        return {
            "id": self.id,
            "event_type": self.event_type,
            "source": self.source,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "has_error": bool(self.error_message)
        }
    
    def is_successful(self) -> bool:
        """Проверка успешности обработки вебхука."""
        return self.status == "success"
    
    def is_failed(self) -> bool:
        """Проверка неудачной обработки вебхука."""
        return self.status == "error"
    
    def is_processing(self) -> bool:
        """Проверка что вебхук в процессе обработки."""
        return self.status == "processing"
    
    def mark_as_successful(self, processed_payload: str) -> None:
        """
        Отметить вебхук как успешно обработанный.
        
        Args:
            processed_payload: Обработанные и валидированные данные
        """
        self.status = "success"
        self.payload = processed_payload
        self.error_message = None
    
    def mark_as_failed(self, error_message: str) -> None:
        """
        Отметить вебхук как неудачно обработанный.
        
        Args:
            error_message: Сообщение об ошибке
        """
        self.status = "error"
        self.error_message = error_message
    
    @classmethod
    def create_processing(cls, event_type: str, source: str, payload: str) -> "WebhookLogModel":
        """
        Фабричный метод для создания записи в статусе обработки.
        
        Args:
            event_type: Тип события
            source: Источник вебхука
            payload: Сырые данные
            
        Returns:
            WebhookLogModel: Новая запись в статусе processing
        """
        return cls(
            id=str(uuid.uuid4()),  # Явно генерируем UUID
            event_type=event_type,
            source=source,
            status="processing",
            payload=payload,
            error_message=None
        )