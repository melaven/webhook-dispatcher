"""
Unit тесты для Pydantic схем валидации.

Тестирует корректность валидационных правил и бизнес-ограничений.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
import sys
import os

# Добавляем корневую папку проекта в Python path  
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.schemas import (
    LeadCreatedData,
    LeadWebhookRequest, 
    PaymentSucceededData,
    PaymentWebhookRequest,
    OrderCreatedData,
    OrderWebhookRequest,
    OrderItem,
    GenericWebhookPayload,
    WebhookResponse
)


class TestLeadCreatedData:
    """Тесты валидации данных лида."""
    
    def test_valid_lead_data(self):
        """Тест валидных данных лида."""
        data = LeadCreatedData(
            name="Иван Петров",
            phone="+7 (999) 123-45-67",
            email="ivan@example.com"
        )
        
        assert data.name == "Иван Петров"
        assert data.phone == "+7 (999) 123-45-67"
        assert data.email == "ivan@example.com"
        assert data.metadata == {}
    
    def test_lead_name_validation(self):
        """Тест валидации имени."""
        # Валидные имена
        valid_names = ["Иван", "Мария Петрова", "John Smith", "李明", "José María"]
        for name in valid_names:
            data = LeadCreatedData(name=name, phone="+79991234567")
            assert data.name.strip() == name.strip()
        
        # Невалидные имена
        invalid_names = ["", "   ", "123", "___", "!@#$%"]
        for name in invalid_names:
            with pytest.raises(ValidationError):
                LeadCreatedData(name=name, phone="+79991234567")
    
    def test_lead_phone_validation(self):
        """Тест валидации телефона."""
        # Валидные телефоны
        valid_phones = [
            "+79991234567",
            "+7 (999) 123-45-67", 
            "89991234567",
            "7-999-123-4567"
        ]
        for phone in valid_phones:
            data = LeadCreatedData(name="Test", phone=phone)
            assert data.phone == phone
        
        # Невалидные телефоны
        invalid_phones = ["123", "abc", "", "+7999123456789012345"]
        for phone in invalid_phones:
            with pytest.raises(ValidationError):
                LeadCreatedData(name="Test", phone=phone)
    
    def test_lead_metadata_size_limit(self):
        """Тест ограничения размера метаданных."""
        # Нормальные метаданные
        normal_metadata = {"source": "landing", "utm_campaign": "summer2024"}
        data = LeadCreatedData(
            name="Test", 
            phone="+79991234567",
            metadata=normal_metadata
        )
        assert data.metadata == normal_metadata
        
        # Слишком большие метаданные
        huge_metadata = {"data": "x" * 15000}  # > 10KB
        with pytest.raises(ValidationError):
            LeadCreatedData(name="Test", phone="+79991234567", metadata=huge_metadata)


class TestLeadWebhookRequest:
    """Тесты полного вебхука лида."""
    
    def test_valid_lead_webhook(self):
        """Тест валидного вебхука лида."""
        webhook = LeadWebhookRequest(
            event_type="lead.created",
            timestamp=1726480000,
            source="tilda",
            data={
                "name": "Максим Тестовый",
                "phone": "+79991234567",
                "email": "test@example.com"
            }
        )
        
        assert webhook.event_type == "lead.created"
        assert webhook.source == "tilda"
        assert webhook.data.name == "Максим Тестовый"
    
    def test_invalid_event_type(self):
        """Тест неправильного типа события."""
        with pytest.raises(ValidationError):
            LeadWebhookRequest(
                event_type="payment.succeeded",  # Неправильный тип
                timestamp=1726480000,
                source="tilda",
                data={
                    "name": "Test",
                    "phone": "+79991234567"
                }
            )
    
    def test_timestamp_validation(self):
        """Тест валидации timestamp."""
        current_time = int(datetime.now().timestamp())
        
        # Валидный timestamp (прошлое и настоящее)
        valid_timestamps = [1726480000, current_time, current_time - 3600]
        for ts in valid_timestamps:
            webhook = LeadWebhookRequest(
                event_type="lead.created",
                timestamp=ts,
                source="test",
                data={"name": "Test", "phone": "+79991234567"}
            )
            assert webhook.timestamp == ts
        
        # Невалидный timestamp (далекое будущее)
        future_timestamp = current_time + 7200  # +2 часа
        with pytest.raises(ValidationError):
            LeadWebhookRequest(
                event_type="lead.created",
                timestamp=future_timestamp,
                source="test",
                data={"name": "Test", "phone": "+79991234567"}
            )


class TestPaymentSucceededData:
    """Тесты валидации данных платежа."""
    
    def test_valid_payment_data(self):
        """Тест валидных данных платежа."""
        data = PaymentSucceededData(
            transaction_id="txn_12345",
            amount=999.99,
            currency="RUB",
            customer_email="customer@example.com"
        )
        
        assert data.transaction_id == "txn_12345"
        assert data.amount == 999.99
        assert data.currency == "RUB"
    
    def test_amount_validation(self):
        """Тест валидации суммы."""
        # Валидные суммы
        valid_amounts = [0.01, 100.00, 999.99, 50000.00]
        for amount in valid_amounts:
            data = PaymentSucceededData(
                transaction_id="test",
                amount=amount,
                customer_email="test@example.com"
            )
            assert data.amount == round(amount, 2)
        
        # Невалидные суммы
        invalid_amounts = [0, -100, 1000001]  # 0, отрицательная, слишком большая
        for amount in invalid_amounts:
            with pytest.raises(ValidationError):
                PaymentSucceededData(
                    transaction_id="test",
                    amount=amount,
                    customer_email="test@example.com"
                )
    
    def test_currency_validation(self):
        """Тест валидации валюты."""
        # Валидные валюты
        valid_currencies = ["RUB", "USD", "EUR", "GBP"]
        for currency in valid_currencies:
            data = PaymentSucceededData(
                transaction_id="test",
                amount=100.00,
                currency=currency,
                customer_email="test@example.com"
            )
            assert data.currency == currency
        
        # Невалидные валюты
        invalid_currencies = ["rub", "RUBLES", "€", "123"]
        for currency in invalid_currencies:
            with pytest.raises(ValidationError):
                PaymentSucceededData(
                    transaction_id="test",
                    amount=100.00,
                    currency=currency,
                    customer_email="test@example.com"
                )


class TestOrderCreatedData:
    """Тесты валидации данных заказа."""
    
    def test_valid_order_data(self):
        """Тест валидных данных заказа."""
        items = [
            OrderItem(name="Товар 1", quantity=2, price=500.00),
            OrderItem(name="Товар 2", quantity=1, price=300.00)
        ]
        
        data = OrderCreatedData(
            order_id="order_12345",
            customer_email="customer@example.com",
            amount=1300.00,  # 2*500 + 1*300
            currency="RUB",
            items=items
        )
        
        assert data.order_id == "order_12345"
        assert data.amount == 1300.00
        assert len(data.items) == 2
    
    def test_order_items_sum_validation(self):
        """Тест валидации суммы товаров."""
        items = [
            OrderItem(name="Товар", quantity=2, price=100.00)
        ]
        
        # Правильная сумма
        data = OrderCreatedData(
            order_id="test",
            customer_email="test@example.com",
            amount=200.00,  # 2 * 100
            items=items
        )
        assert data.amount == 200.00
        
        # Неправильная сумма
        with pytest.raises(ValidationError):
            OrderCreatedData(
                order_id="test",
                customer_email="test@example.com",
                amount=150.00,  # Не совпадает с 2*100
                items=items
            )


class TestOrderItem:
    """Тесты валидации элемента заказа."""
    
    def test_valid_order_item(self):
        """Тест валидного товара."""
        item = OrderItem(
            name="Смартфон Apple iPhone",
            quantity=1,
            price=99999.99
        )
        
        assert item.name == "Смартфон Apple iPhone"
        assert item.quantity == 1
        assert item.price == 99999.99
    
    def test_quantity_validation(self):
        """Тест валидации количества."""
        # Валидное количество
        item = OrderItem(name="Test", quantity=5, price=100.0)
        assert item.quantity == 5
        
        # Невалидное количество
        with pytest.raises(ValidationError):
            OrderItem(name="Test", quantity=0, price=100.0)


class TestGenericWebhookPayload:
    """Тесты универсальной схемы вебхука."""
    
    def test_generic_payload(self):
        """Тест универсального payload."""
        webhook = GenericWebhookPayload(
            event_type="custom.event",
            timestamp=1726480000,
            source="custom_system",
            data={
                "custom_field": "custom_value",
                "nested": {
                    "field": "value"
                }
            }
        )
        
        assert webhook.event_type == "custom.event"
        assert webhook.data["custom_field"] == "custom_value"
    
    def test_data_size_limit(self):
        """Тест ограничения размера данных."""
        # Слишком большие данные
        huge_data = {"field": "x" * 60000}  # > 50KB
        
        with pytest.raises(ValidationError):
            GenericWebhookPayload(
                event_type="test",
                timestamp=1726480000,
                source="test",
                data=huge_data
            )


class TestWebhookResponse:
    """Тесты схемы ответа."""
    
    def test_webhook_response(self):
        """Тест корректного ответа."""
        response = WebhookResponse(
            status="success",
            message="Webhook processed successfully",
            event="lead.created",
            webhook_id="123e4567-e89b-12d3-a456-426614174000"
        )
        
        assert response.status == "success"
        assert response.processed == True  # Значение по умолчанию
        assert response.event == "lead.created"
        assert response.webhook_id == "123e4567-e89b-12d3-a456-426614174000"
        assert response.timestamp is not None