"""
Pydantic Schemas для Webhook Dispatcher.

Определяет контракты API и валидационные схемы для входящих/исходящих данных.
Следует принципам Clean Architecture - изолированы от бизнес-логики.
"""

from pydantic import BaseModel, Field, EmailStr, validator, root_validator
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Перечисление поддерживаемых типов событий."""
    LEAD_CREATED = "lead.created"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    ORDER_CREATED = "order.created"


class WebhookStatus(str, Enum):
    """Статусы обработки вебхука."""
    PROCESSING = "processing"
    SUCCESS = "success"
    ERROR = "error"


# ============== Базовые схемы ==============

class BaseWebhookPayload(BaseModel):
    """
    Базовая схема для любого входящего вебхука.
    
    Содержит минимально необходимые поля для всех типов вебхуков.
    """
    event_type: str = Field(
        ..., 
        description="Тип события",
        example="lead.created",
        min_length=3,
        max_length=100
    )
    timestamp: int = Field(
        ..., 
        description="Unix timestamp отправки события",
        example=1726480000,
        ge=0
    )
    source: str = Field(
        ..., 
        description="Источник вебхука",
        example="tilda",
        min_length=2,
        max_length=50
    )
    
    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Валидация timestamp - не должен быть из будущего."""
        current_timestamp = int(datetime.now().timestamp())
        if v > current_timestamp + 3600:  # +1 час на часовые пояса
            raise ValueError('Timestamp не может быть из далекого будущего')
        return v
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "event_type": "lead.created",
                "timestamp": 1726480000,
                "source": "tilda"
            }
        }


class WebhookResponse(BaseModel):
    """Стандартный ответ API на обработку вебхука."""
    
    status: str = Field(..., description="Статус обработки", example="success")
    message: str = Field(..., description="Сообщение о результате")
    event: Optional[str] = Field(None, description="Тип обработанного события")
    processed: bool = Field(True, description="Флаг успешной обработки")
    webhook_id: Optional[str] = Field(None, description="UUID обработанного вебхука")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Время ответа сервера"
    )
    
    class Config:
        """Конфигурация модели."""
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": "Вебхук успешно обработан",
                "event": "lead.created",
                "processed": True,
                "webhook_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "timestamp": "2024-09-16T12:00:00"
            }
        }


# ============== Схемы для лидов ==============

class LeadCreatedData(BaseModel):
    """Данные о созданном лиде с строгой валидацией."""
    
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        description="Имя клиента",
        example="Иван Петров"
    )
    phone: str = Field(
        ..., 
        description="Телефон клиента",
        example="+7 (999) 123-45-67",
        pattern=r'^(\+7|8|7)[\s\-]?(\(?\d{3}\)?)[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$'
    )
    email: Optional[EmailStr] = Field(
        None, 
        description="Email клиента",
        example="ivan@example.com"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Дополнительные метаданные"
    )
    
    @validator('name')
    def validate_name(cls, v):
        """Валидация имени - только буквы и базовые символы."""
        if not v.strip():
            raise ValueError('Имя не может быть пустым')
        
        # Проверяем что есть хотя бы одна буква
        if not any(c.isalpha() for c in v):
            raise ValueError('Имя должно содержать хотя бы одну букву')
        
        return v.strip()
    
    @validator('phone')
    def validate_phone(cls, v):
        """Дополнительная валидация телефона."""
        # Убираем все нецифровые символы кроме + в начале
        import re
        cleaned = re.sub(r'[^\d+]', '', v)
        
        # Проверяем длину цифр (должно быть 10-11 цифр)
        digits_only = re.sub(r'[^\d]', '', cleaned)
        
        if len(digits_only) < 10:
            raise ValueError('Номер телефона слишком короткий')
        if len(digits_only) > 11:
            raise ValueError('Номер телефона слишком длинный')
            
        # Проверяем что номер начинается правильно
        if cleaned.startswith('+7'):
            if len(digits_only) != 11 or not digits_only.startswith('7'):
                raise ValueError('Некорректный российский номер')
        elif cleaned.startswith('8'):
            if len(digits_only) != 11:
                raise ValueError('Некорректный российский номер')
        elif cleaned.startswith('7') and not cleaned.startswith('+'):
            if len(digits_only) != 11:
                raise ValueError('Некорректный российский номер')
        
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Валидация метаданных - ограничение размера."""
        if v and len(str(v)) > 10000:  # 10KB лимит
            raise ValueError('Метаданные слишком большие')
        return v


class LeadWebhookRequest(BaseWebhookPayload):
    """Запрос на создание лида."""
    
    data: LeadCreatedData
    
    @validator('event_type')
    def validate_event_type(cls, v):
        """Валидация типа события для лидов."""
        if v != EventType.LEAD_CREATED:
            raise ValueError(f'Ожидается {EventType.LEAD_CREATED}, получен {v}')
        return v


# ============== Схемы для платежей ==============

class PaymentSucceededData(BaseModel):
    """Данные об успешной оплате."""
    
    transaction_id: str = Field(
        ..., 
        description="Уникальный ID транзакции",
        example="txn_1234567890",
        min_length=1,
        max_length=100
    )
    amount: float = Field(
        ..., 
        gt=0, 
        description="Сумма платежа",
        example=999.99
    )
    currency: str = Field(
        default="RUB", 
        description="Валюта платежа",
        example="RUB",
        pattern=r'^[A-Z]{3}$'
    )
    customer_email: EmailStr = Field(
        ..., 
        description="Email покупателя",
        example="customer@example.com"
    )
    order_id: Optional[str] = Field(
        None, 
        description="ID заказа в системе",
        max_length=100
    )
    
    @validator('amount')
    def validate_amount(cls, v):
        """Валидация суммы - разумные пределы."""
        if v > 1000000:  # 1 млн лимит
            raise ValueError('Сумма слишком большая')
        if v < 0.01:
            raise ValueError('Сумма слишком маленькая')
        return round(v, 2)  # Округляем до копеек


class PaymentWebhookRequest(BaseWebhookPayload):
    """Запрос об успешной оплате."""
    
    data: PaymentSucceededData
    
    @validator('event_type')
    def validate_event_type(cls, v):
        """Валидация типа события для платежей."""
        if v != EventType.PAYMENT_SUCCEEDED:
            raise ValueError(f'Ожидается {EventType.PAYMENT_SUCCEEDED}, получен {v}')
        return v


# ============== Схемы для заказов ==============

class OrderItem(BaseModel):
    """Элемент заказа."""
    
    name: str = Field(..., min_length=1, max_length=200, description="Название товара")
    quantity: int = Field(..., ge=1, description="Количество")
    price: float = Field(..., ge=0, description="Цена за единицу")
    
    @validator('price')
    def validate_price(cls, v):
        """Валидация цены товара."""
        return round(v, 2)


class OrderCreatedData(BaseModel):
    """Данные о созданном заказе."""
    
    order_id: str = Field(
        ..., 
        description="Уникальный ID заказа",
        example="order_12345",
        min_length=3,
        max_length=100
    )
    customer_email: EmailStr = Field(
        ..., 
        description="Email покупателя",
        example="customer@example.com"
    )
    amount: float = Field(
        ..., 
        gt=0, 
        description="Общая сумма заказа",
        example=1299.00
    )
    currency: str = Field(
        default="RUB", 
        description="Валюта",
        pattern=r'^[A-Z]{3}$'
    )
    items: Optional[List[OrderItem]] = Field(
        default_factory=list,
        description="Товары в заказе"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Дополнительные данные заказа"
    )
    
    @validator('items')
    def validate_items(cls, v, values):
        """Валидация товаров - проверка суммы."""
        if v:
            calculated_total = sum(item.price * item.quantity for item in v)
            expected_total = values.get('amount', 0)
            
            # Допускаем небольшую погрешность из-за округления
            if abs(calculated_total - expected_total) > 0.01:
                raise ValueError(f'Сумма товаров ({calculated_total}) не совпадает с общей суммой ({expected_total})')
        
        return v


class OrderWebhookRequest(BaseWebhookPayload):
    """Запрос о созданном заказе."""
    
    data: OrderCreatedData
    
    @validator('event_type')
    def validate_event_type(cls, v):
        """Валидация типа события для заказов."""
        if v != EventType.ORDER_CREATED:
            raise ValueError(f'Ожидается {EventType.ORDER_CREATED}, получен {v}')
        return v


# ============== Универсальная схема ==============

class GenericWebhookPayload(BaseWebhookPayload):
    """Универсальная схема для неизвестных типов вебхуков."""
    
    data: Dict[str, Any] = Field(..., description="Произвольные данные")
    
    @validator('data')
    def validate_data_size(cls, v):
        """Валидация размера данных."""
        if len(str(v)) > 50000:  # 50KB лимит
            raise ValueError('Данные слишком большие')
        return v


# ============== Схемы для статистики ==============

class WebhookStatistics(BaseModel):
    """Статистика по обработанным вебхукам."""
    
    total_webhooks: int = Field(..., description="Общее количество вебхуков")
    status_breakdown: Dict[str, int] = Field(..., description="Разбивка по статусам")
    event_type_breakdown: Dict[str, int] = Field(..., description="Разбивка по типам событий")
    timestamp: str = Field(..., description="Время формирования статистики")


class SecurityConfigResponse(BaseModel):
    """Ответ с конфигурацией безопасности."""
    
    security_config: Dict[str, Any] = Field(..., description="Настройки безопасности")
    authenticated: bool = Field(..., description="Статус аутентификации")
    timestamp: str = Field(..., description="Время ответа")


# ============== Union типы для автоматического определения ==============

WebhookRequest = Union[LeadWebhookRequest, PaymentWebhookRequest, OrderWebhookRequest, GenericWebhookPayload]