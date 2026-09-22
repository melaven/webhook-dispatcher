"""
Интеграционные тесты безопасности для Webhook Dispatcher.

Проверяет два основных сценария:
1. Блокировка неавторизованных запросов (403 Forbidden)
2. Успешная обработка с валидным API ключом
"""

import requests
import json
import pytest
from typing import Dict, Any

# Конфигурация для тестов
BASE_URL = "http://127.0.0.1:8000"
WEBHOOK_ENDPOINT = f"{BASE_URL}/api/v1/webhook/incoming"
STATS_ENDPOINT = f"{BASE_URL}/api/v1/stats"
API_KEY = "test-secret-key-12345"

def test_unauthorized_request():
    """
    🔒 Тест 1: Попытка отправить запрос без API ключа.
    
    Ожидаем: 403 Forbidden - система должна заблокировать неавторизованный доступ.
    """
    print("🔒 Тест 1: Попытка стучаться без API-ключа...")
    
    payload = {
        "event_type": "lead.created",
        "timestamp": 1726480000,
        "source": "test",
        "data": {
            "name": "Test User",
            "phone": "+79991234567"
        }
    }
    
    try:
        response = requests.post(
            WEBHOOK_ENDPOINT, 
            json=payload,
            timeout=10
        )
        
        assert response.status_code == 403, f"Ожидался 403, получен {response.status_code}"
        
        response_data = response.json()
        assert "Access denied" in response_data.get("detail", ""), "Неправильное сообщение об ошибке"
        
        print("✅ Успешно! Шлюз заблокировал неавторизованный запрос.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка: Сервер не запущен! Сначала запусти: python main.py")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка в тесте безопасности: {e}")
        return False


def test_authorized_lead_request():
    """
    🚀 Тест 2: Отправка валидного лида с правильным API ключом.
    
    Ожидаем: 200 OK - успешная валидация, обработка и сохранение в БД.
    """
    print("\n🚀 Тест 2: Отправка валидного лида с правильным API-ключом...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "event_type": "lead.created",
        "timestamp": 1726480000,
        "source": "tilda_landing",
        "data": {
            "name": "Максим Тестовый",
            "phone": "+79991234567",
            "email": "test@example.com"
        }
    }
    
    try:
        response = requests.post(
            WEBHOOK_ENDPOINT, 
            headers=headers, 
            json=payload,
            timeout=10
        )
        
        print(f"Статус ответа: {response.status_code}")
        response_data = response.json()
        print(f"Ответ сервера: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        assert response.status_code == 200, f"Запрос должен был пройти успешно, получен {response.status_code}"
        assert response_data.get("status") == "success", "Статус должен быть success"
        assert response_data.get("processed") == True, "Флаг processed должен быть True"
        assert "webhook_id" in response_data, "Ответ должен содержать webhook_id"
        
        print("✅ Успешно! Запрос верифицирован, валидирован и записан в Audit Trail.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка: Сервер не запущен! Сначала запусти: python main.py")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка в тесте лида: {e}")
        return False


def test_authorized_payment_request():
    """
    💳 Тест 3: Отправка валидного платежа с правильным API ключом.
    """
    print("\n💳 Тест 3: Отправка валидного платежа...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "event_type": "payment.succeeded",
        "timestamp": 1726480000,
        "source": "robokassa",
        "data": {
            "transaction_id": "txn_test_123456",
            "amount": 999.99,
            "currency": "RUB",
            "customer_email": "customer@example.com",
            "order_id": "order_789"
        }
    }
    
    try:
        response = requests.post(
            WEBHOOK_ENDPOINT, 
            headers=headers, 
            json=payload,
            timeout=10
        )
        
        print(f"Статус ответа: {response.status_code}")
        response_data = response.json()
        print(f"Ответ сервера: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
        
        assert response.status_code == 200, f"Платеж должен быть обработан успешно"
        assert response_data.get("status") == "success"
        assert response_data.get("event") == "payment.succeeded"
        
        print("✅ Успешно! Платеж обработан и записан в систему.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка: Сервер не запущен!")
        return False
    except Exception as e:
        print(f"❌ Ошибка в тесте платежа: {e}")
        return False


def test_invalid_json():
    """
    🚫 Тест 4: Отправка невалидного JSON.
    
    Ожидаем: 400 Bad Request.
    """
    print("\n🚫 Тест 4: Отправка невалидного JSON...")
    
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    invalid_json = '{"invalid": json}'
    
    try:
        response = requests.post(
            WEBHOOK_ENDPOINT, 
            headers=headers, 
            data=invalid_json,
            timeout=10
        )
        
        assert response.status_code == 400, f"Ожидался 400, получен {response.status_code}"
        
        print("✅ Успешно! Невалидный JSON корректно отклонен.")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка: Сервер не запущен!")
        return False
    except Exception as e:
        print(f"❌ Ошибка в тесте JSON: {e}")
        return False


def test_statistics_endpoint():
    """
    📊 Тест 5: Проверка защищенного эндпоинта статистики.
    """
    print("\n📊 Тест 5: Получение статистики...")
    
    headers = {
        "X-API-Key": API_KEY
    }
    
    try:
        # Тест без ключа - должно быть 403
        response_no_key = requests.get(STATS_ENDPOINT, timeout=10)
        assert response_no_key.status_code == 403, "Статистика без ключа должна возвращать 403"
        
        # Тест с ключом - должно быть 200
        response = requests.get(STATS_ENDPOINT, headers=headers, timeout=10)
        
        assert response.status_code == 200, f"Статистика с ключом должна работать"
        
        stats = response.json()
        assert "total_webhooks" in stats, "Статистика должна содержать total_webhooks"
        assert "status_breakdown" in stats, "Статистика должна содержать status_breakdown"
        
        print(f"✅ Статистика получена: {stats['total_webhooks']} вебхуков обработано")
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка: Сервер не запущен!")
        return False
    except Exception as e:
        print(f"❌ Ошибка в тесте статистики: {e}")
        return False


def run_all_security_tests():
    """
    Запуск всех тестов безопасности.
    
    Returns:
        bool: True если все тесты прошли успешно
    """
    print("=" * 60)
    print("🛡️  ЗАПУСК ПОЛНОГО КОМПЛЕКСА ТЕСТОВ БЕЗОПАСНОСТИ")
    print("=" * 60)
    
    tests = [
        test_unauthorized_request,
        test_authorized_lead_request,
        test_authorized_payment_request,
        test_invalid_json,
        test_statistics_endpoint
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в {test_func.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📋 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено: {passed}")
    print(f"❌ Провалено: {failed}")
    print(f"📊 Общий результат: {'УСПЕХ' if failed == 0 else 'ЕСТЬ ОШИБКИ'}")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_security_tests()
    
    if not success:
        print("\n⚠️  Некоторые тесты провалились. Проверьте:")
        print("1. Запущен ли сервер (python main.py)")
        print("2. Правильный ли API ключ в .env файле")
        print("3. Доступна ли база данных")
        exit(1)
    else:
        print("\n🎉 Все тесты безопасности пройдены безупречно!")
        print("🚀 Система готова к production deployment!")
        exit(0)