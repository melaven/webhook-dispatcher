"""
Unit тесты для доменных моделей Webhook Dispatcher.

Тестирует бизнес-логику моделей без зависимостей от БД.
"""

import pytest
import uuid
from datetime import datetime
import sys
import os

# Добавляем корневую папку проекта в Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models import WebhookLogModel


class TestWebhookLogModel:
    """Тесты для модели WebhookLogModel."""
    
    def test_create_processing_webhook(self):
        """Тест создания вебхука в статусе processing."""
        webhook = WebhookLogModel.create_processing(
            event_type="lead.created",
            source="tilda",
            payload='{"name": "Test User"}'
        )
        
        assert webhook.event_type == "lead.created"
        assert webhook.source == "tilda"
        assert webhook.status == "processing"
        assert webhook.payload == '{"name": "Test User"}'
        assert webhook.error_message is None
        assert webhook.id is not None  # UUID должен быть сгенерирован
    
    def test_mark_as_successful(self):
        """Тест успешной обработки вебхука."""
        webhook = WebhookLogModel.create_processing(
            event_type="payment.succeeded",
            source="robokassa", 
            payload='{"amount": 100}'
        )
        
        processed_payload = '{"amount": 100, "validated": true}'
        webhook.mark_as_successful(processed_payload)
        
        assert webhook.status == "success"
        assert webhook.payload == processed_payload
        assert webhook.error_message is None
        assert webhook.is_successful() == True
        assert webhook.is_failed() == False
        assert webhook.is_processing() == False
    
    def test_mark_as_failed(self):
        """Тест неудачной обработки вебхука."""
        webhook = WebhookLogModel.create_processing(
            event_type="order.created",
            source="shopify",
            payload='{"invalid": data}'
        )
        
        error_message = "ValidationError: Invalid JSON structure"
        webhook.mark_as_failed(error_message)
        
        assert webhook.status == "error"
        assert webhook.error_message == error_message
        assert webhook.is_failed() == True
        assert webhook.is_successful() == False
        assert webhook.is_processing() == False
    
    def test_status_checks(self):
        """Тест методов проверки статуса."""
        webhook = WebhookLogModel.create_processing(
            event_type="test.event",
            source="test",
            payload="{}"
        )
        
        # Проверяем начальный статус
        assert webhook.is_processing() == True
        assert webhook.is_successful() == False
        assert webhook.is_failed() == False
        
        # Меняем на success
        webhook.mark_as_successful("{}")
        assert webhook.is_processing() == False
        assert webhook.is_successful() == True
        assert webhook.is_failed() == False
        
        # Меняем на error
        webhook.mark_as_failed("Test error")
        assert webhook.is_processing() == False
        assert webhook.is_successful() == False
        assert webhook.is_failed() == True
    
    def test_to_dict(self):
        """Тест сериализации модели в словарь."""
        webhook = WebhookLogModel.create_processing(
            event_type="lead.created",
            source="tilda",
            payload='{"name": "Test"}'
        )
        webhook.created_at = datetime.now()
        
        data = webhook.to_dict()
        
        assert isinstance(data, dict)
        assert data["event_type"] == "lead.created"
        assert data["source"] == "tilda"
        assert data["status"] == "processing"
        assert "id" in data
        assert "created_at" in data
        assert data["has_error"] == False
        
        # Тест с ошибкой
        webhook.mark_as_failed("Test error")
        data_with_error = webhook.to_dict()
        assert data_with_error["has_error"] == True
    
    def test_repr(self):
        """Тест строкового представления модели."""
        webhook = WebhookLogModel.create_processing(
            event_type="payment.succeeded",
            source="stripe",
            payload="{}"
        )
        
        repr_str = repr(webhook)
        
        assert "WebhookLog" in repr_str
        assert "payment.succeeded" in repr_str
        assert "stripe" in repr_str
        assert "processing" in repr_str
    
    def test_uuid_generation(self):
        """Тест что каждая модель получает уникальный UUID."""
        webhook1 = WebhookLogModel.create_processing("test1", "source1", "{}")
        webhook2 = WebhookLogModel.create_processing("test2", "source2", "{}")
        
        assert webhook1.id != webhook2.id
        assert len(webhook1.id) == 36  # Стандартная длина UUID
        assert len(webhook2.id) == 36
        
        # Проверяем что это валидные UUID
        uuid.UUID(webhook1.id)  # Не должно вызвать исключение
        uuid.UUID(webhook2.id)
    
    def test_business_logic_validation(self):
        """Тест бизнес-логики и валидации на уровне модели."""
        # Тест что processing - корректный начальный статус
        webhook = WebhookLogModel.create_processing(
            event_type="test.event",
            source="test_source",
            payload='{"test": "data"}'
        )
        
        assert webhook.status == "processing"
        
        # Тест что после успешной обработки нельзя снова пометить как processing
        webhook.mark_as_successful('{"processed": true}')
        
        # В реальной системе здесь могла бы быть дополнительная валидация
        # Например, проверка что статус не меняется с success на processing
        
        # Тест сброса ошибки при успешной обработке
        webhook_with_error = WebhookLogModel.create_processing("test", "test", "{}")
        webhook_with_error.mark_as_failed("Some error")
        assert webhook_with_error.error_message == "Some error"
        
        webhook_with_error.mark_as_successful("{}")
        assert webhook_with_error.error_message is None