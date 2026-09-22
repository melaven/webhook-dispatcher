# 🛡️ Защита от Replay-атак в Webhook Dispatcher

## 🎯 Что такое Replay-атака?

**Replay-атака** (атака повторного воспроизведения) - это тип кибератаки, при которой злоумышленник перехватывает валидный сетевой запрос и многократно отправляет его повторно.

### 📊 Пример сценария атаки:

1. **Клиент отправляет валидный вебхук:**
   ```http
   POST /api/v1/webhook/incoming
   X-API-Key: valid-key-12345
   X-Hub-Signature-256: sha256=valid-hmac-signature
   
   {"event_type": "payment.succeeded", "amount": 1000, "order_id": "12345"}
   ```

2. **Хакер перехватывает запрос** (например, через MITM атаку)

3. **Хакер отправляет тот же запрос 1000 раз:**
   - Все 1000 запросов имеют корректный API ключ ✅
   - Все 1000 запросов имеют корректную HMAC подпись ✅
   - **БЕЗ защиты от replay**: сервер обработает все 1000 запросов! ❌
   - **С защитой от replay**: сервер обработает только первый запрос! ✅

---

## 🛡️ Наша защита от Replay-атак

### 🕒 Двухуровневая система защиты:

#### 1. **Timestamp Validation** (Проверка времени)
```http
X-Timestamp: 1726480000
```
- **Цель**: Отклонять устаревшие запросы
- **Логика**: Запросы старше 5 минут автоматически отклоняются
- **Защищает от**: Повторного воспроизведения "старых" перехваченных запросов

#### 2. **Nonce Validation** (Проверка уникальности)
```http
X-Nonce: unique-request-id-1234567890abcdef
```
- **Цель**: Гарантировать уникальность каждого запроса
- **Логика**: Каждый nonce можно использовать только один раз
- **Защищает от**: Повторной отправки одного и того же запроса

---

## 🔧 Техническая реализация

### 🏗️ Архитектурные компоненты:

#### 1. **ReplayProtectionCache**
```python
class ReplayProtectionCache:
    """Thread-safe кеш для хранения использованных nonce"""
    
    def add_nonce(self, nonce: str) -> bool:
        """Добавляет nonce в кеш, возвращает False если уже существует"""
    
    def is_nonce_used(self, nonce: str) -> bool:
        """Проверяет использовался ли nonce ранее"""
```

**Возможности:**
- ✅ Thread-safe операции с блокировками
- ✅ Автоматическая очистка устаревших записей
- ✅ Ограничение размера кеша (10,000 записей по умолчанию)
- ✅ Статистика использования и производительности

#### 2. **SecurityService.verify_replay_protection()**
```python
def verify_replay_protection(self, timestamp: str, nonce: str) -> bool:
    """Комплексная проверка timestamp + nonce"""
    
    # 1. Проверка timestamp
    if not self.verify_timestamp(timestamp):
        return False
    
    # 2. Проверка nonce
    if not self.verify_nonce(nonce):
        return False
        
    return True
```

#### 3. **FastAPI Dependency**
```python
async def verify_replay_protection(
    timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    nonce: Optional[str] = Header(None, alias="X-Nonce")
) -> bool:
    """FastAPI dependency для автоматической проверки"""
```

---

## 📋 Требования к клиентам

### ✅ Обязательные заголовки:

```http
POST /api/v1/webhook/incoming HTTP/1.1
Host: webhook-dispatcher.com
Content-Type: application/json
X-API-Key: your-secret-api-key-here
X-Timestamp: 1726480000
X-Nonce: unique-request-id-32-chars-min
X-Hub-Signature-256: sha256=computed-hmac-signature

{
  "event_type": "lead.created",
  "timestamp": 1726480000,
  "source": "your_system",
  "data": {
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

### 📏 Требования к заголовкам:

#### **X-Timestamp**
- **Формат**: Unix timestamp (секунды с 1970-01-01)
- **Генерация**: `Math.floor(Date.now() / 1000)` (JavaScript)
- **Ограничения**: 
  - Не более 5 минут в прошлом
  - Не более 1 минуты в будущем (учитывает clock skew)

#### **X-Nonce** 
- **Формат**: Любая строка минимум 16 символов
- **Генерация**: UUID, random hex, или custom ID
- **Требования**:
  - Уникальность в пределах временного окна
  - Криптографически стойкая генерация (рекомендуется)

---

## 💻 Примеры клиентского кода

### 🟨 JavaScript/Node.js

```javascript
const crypto = require('crypto');

function createSecureWebhookRequest(payload) {
  const timestamp = Math.floor(Date.now() / 1000);
  const nonce = crypto.randomUUID().replace(/-/g, ''); // UUID без дефисов
  
  const body = JSON.stringify(payload);
  
  // HMAC подпись (опционально)
  const hmacSignature = crypto
    .createHmac('sha256', process.env.WEBHOOK_SECRET)
    .update(body)
    .digest('hex');
  
  return {
    method: 'POST',
    url: 'https://webhook-dispatcher.com/api/v1/webhook/incoming',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.DISPATCHER_API_KEY,
      'X-Timestamp': timestamp.toString(),
      'X-Nonce': nonce,
      'X-Hub-Signature-256': `sha256=${hmacSignature}`
    },
    body: body
  };
}

// Использование
const webhookData = {
  event_type: 'lead.created',
  timestamp: Math.floor(Date.now() / 1000),
  source: 'my_app',
  data: { name: 'John Doe', email: 'john@example.com' }
};

const request = createSecureWebhookRequest(webhookData);
// Отправляем request через fetch, axios, etc.
```

### 🐍 Python

```python
import time
import hmac
import hashlib
import uuid
import json
import requests

def create_secure_webhook_request(payload: dict) -> dict:
    timestamp = str(int(time.time()))
    nonce = uuid.uuid4().hex  # 32-символьный hex string
    
    body = json.dumps(payload, separators=(',', ':'))
    
    # HMAC подпись (опционально)
    webhook_secret = os.getenv('WEBHOOK_SECRET').encode('utf-8')
    hmac_signature = hmac.new(
        webhook_secret,
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return {
        'method': 'POST',
        'url': 'https://webhook-dispatcher.com/api/v1/webhook/incoming',
        'headers': {
            'Content-Type': 'application/json',
            'X-API-Key': os.getenv('DISPATCHER_API_KEY'),
            'X-Timestamp': timestamp,
            'X-Nonce': nonce,
            'X-Hub-Signature-256': f'sha256={hmac_signature}'
        },
        'data': body
    }

# Использование
webhook_data = {
    "event_type": "payment.succeeded",
    "timestamp": int(time.time()),
    "source": "my_payment_system",
    "data": {
        "transaction_id": "txn_123456",
        "amount": 99.99,
        "currency": "USD"
    }
}

request_config = create_secure_webhook_request(webhook_data)
response = requests.post(
    request_config['url'],
    headers=request_config['headers'],
    data=request_config['data']
)
```

### 🐘 PHP

```php
<?php

function createSecureWebhookRequest(array $payload): array {
    $timestamp = (string) time();
    $nonce = bin2hex(random_bytes(16)); // 32-символьный hex
    
    $body = json_encode($payload, JSON_UNESCAPED_SLASHES);
    
    // HMAC подпись (опционально)
    $webhookSecret = $_ENV['WEBHOOK_SECRET'];
    $hmacSignature = hash_hmac('sha256', $body, $webhookSecret);
    
    return [
        'method' => 'POST',
        'url' => 'https://webhook-dispatcher.com/api/v1/webhook/incoming',
        'headers' => [
            'Content-Type: application/json',
            'X-API-Key: ' . $_ENV['DISPATCHER_API_KEY'],
            'X-Timestamp: ' . $timestamp,
            'X-Nonce: ' . $nonce,
            'X-Hub-Signature-256: sha256=' . $hmacSignature
        ],
        'body' => $body
    ];
}

// Использование
$webhookData = [
    'event_type' => 'order.created',
    'timestamp' => time(),
    'source' => 'my_ecommerce',
    'data' => [
        'order_id' => 'ord_789',
        'amount' => 149.99,
        'customer_email' => 'customer@example.com'
    ]
];

$requestConfig = createSecureWebhookRequest($webhookData);

// Отправляем через cURL или Guzzle
$ch = curl_init();
curl_setopt($ch, CURLOPT_URL, $requestConfig['url']);
curl_setopt($ch, CURLOPT_HTTPHEADER, $requestConfig['headers']);
curl_setopt($ch, CURLOPT_POSTFIELDS, $requestConfig['body']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

$response = curl_exec($ch);
curl_close($ch);
?>
```

---

## ⚙️ Конфигурация и настройка

### 🔧 Environment Variables

```bash
# Включение/выключение защиты от replay-атак
REPLAY_PROTECTION_ENABLED=true

# Максимальный возраст timestamp (секунды)
MAX_TIMESTAMP_AGE_SECONDS=300  # 5 минут

# Размер кеша nonce
NONCE_CACHE_SIZE=10000

# Интервал очистки кеша (секунды) 
NONCE_CLEANUP_INTERVAL=3600  # 1 час
```

### 📊 Мониторинг и статистика

#### **API эндпоинт для статистики:**
```http
GET /api/v1/security/replay-stats
X-API-Key: your-api-key

Response:
{
  "replay_protection_enabled": true,
  "total_nonces": 2547,
  "max_size": 10000,
  "cache_usage_percent": 25.47,
  "max_timestamp_age_seconds": 300,
  "last_cleanup": "2026-09-16T15:30:00Z"
}
```

#### **Логи безопасности:**
```
2026-09-16 15:30:15 INFO  ✅ Timestamp валиден (возраст: 23.45s)
2026-09-16 15:30:15 INFO  ✅ Nonce уникален и добавлен в кеш: a1b2c3d4e5f6...
2026-09-16 15:30:15 INFO  🛡️ Запрос прошел полную защиту от replay-атак

2026-09-16 15:35:42 WARN  🛡️ REPLAY-АТАКА ОБНАРУЖЕНА! Nonce уже использовался: x9y8z7w6v5u4...
2026-09-16 15:36:18 WARN  🛡️ Устаревший timestamp: 367.23s > 300s - возможная replay-атака
```

---

## 🧪 Тестирование защиты

### 🔍 Unit тесты
```bash
# Запуск тестов защиты от replay-атак
python -m pytest tests/test_replay_protection.py -v

# Запуск специфических тестов
python tests/test_replay_protection.py
```

### 🌐 Интеграционные тесты

#### **Тест 1: Валидный запрос**
```bash
curl -X POST http://localhost:8000/api/v1/webhook/incoming \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-secret-key-12345" \
  -H "X-Timestamp: $(date +%s)" \
  -H "X-Nonce: $(openssl rand -hex 16)" \
  -d '{"event_type":"lead.created","timestamp":1726480000,"source":"test","data":{"name":"Test","phone":"+1234567890"}}'

# Ожидаем: HTTP 200 OK
```

#### **Тест 2: Replay-атака (повторный nonce)**
```bash
# Сохраняем nonce для повторного использования
NONCE=$(openssl rand -hex 16)

# Первый запрос
curl -X POST http://localhost:8000/api/v1/webhook/incoming \
  -H "X-API-Key: test-secret-key-12345" \
  -H "X-Timestamp: $(date +%s)" \
  -H "X-Nonce: $NONCE" \
  -d '{"event_type":"lead.created","data":{"name":"Test1","phone":"+1234567890"}}'

# Второй запрос с тем же nonce (replay-атака)
curl -X POST http://localhost:8000/api/v1/webhook/incoming \
  -H "X-API-Key: test-secret-key-12345" \
  -H "X-Timestamp: $(date +%s)" \
  -H "X-Nonce: $NONCE" \
  -d '{"event_type":"lead.created","data":{"name":"Test2","phone":"+1234567890"}}'

# Ожидаем: Первый HTTP 200 OK, Второй HTTP 409 Conflict
```

#### **Тест 3: Устаревший timestamp**
```bash
# Timestamp 10 минут назад
OLD_TIMESTAMP=$(($(date +%s) - 600))

curl -X POST http://localhost:8000/api/v1/webhook/incoming \
  -H "X-API-Key: test-secret-key-12345" \
  -H "X-Timestamp: $OLD_TIMESTAMP" \
  -H "X-Nonce: $(openssl rand -hex 16)" \
  -d '{"event_type":"lead.created","data":{"name":"Test","phone":"+1234567890"}}'

# Ожидаем: HTTP 409 Conflict
```

---

## 🚨 Коды ошибок и их обработка

### 🔴 HTTP 409 Conflict - Replay Attack Detected

**Возможные причины:**
1. **Повторный nonce**: Тот же nonce уже использовался
2. **Устаревший timestamp**: Timestamp старше 5 минут  
3. **Timestamp из будущего**: Timestamp более чем на 1 минуту в будущем
4. **Отсутствующие заголовки**: Нет X-Timestamp или X-Nonce

**Пример ответа:**
```json
{
  "detail": "Replay attack detected: Request already processed or expired"
}
```

**Рекомендации по обработке:**
- ✅ **НЕ повторяйте** запрос с теми же заголовками
- ✅ **Сгенерируйте новый** X-Nonce
- ✅ **Обновите** X-Timestamp до текущего времени
- ✅ **Логируйте** инцидент для расследования

---

## 📈 Производительность и масштабирование

### 🏎️ Характеристики производительности:

#### **Память:**
- **Nonce кеш**: ~100 байт на запись
- **10,000 nonce**: ~1MB RAM
- **100,000 nonce**: ~10MB RAM

#### **CPU:**
- **Проверка timestamp**: O(1) - константное время
- **Проверка nonce**: O(1) - хеш-таблица lookup
- **Очистка кеша**: O(n) - каждый час

#### **Latency:**
- **Добавочная задержка**: <1ms на запрос
- **Влияние на throughput**: Минимальное

### 🔧 Настройка для высоких нагрузок:

#### **Для 100,000+ RPS:**
```bash
# Увеличиваем размер кеша
NONCE_CACHE_SIZE=100000

# Чаще очищаем устаревшие записи  
NONCE_CLEANUP_INTERVAL=1800  # 30 минут

# Сокращаем временное окно для экономии памяти
MAX_TIMESTAMP_AGE_SECONDS=180  # 3 минуты
```

#### **Для распределенных систем:**
- **Redis кеш**: Вместо локального кеша для кластерной работы
- **Database nonce store**: Для персистентности между перезапусками  
- **Rate limiting**: Дополнительная защита от DDoS через replay-атаки

---

## 🔒 Безопасность и лучшие практики

### ✅ Best Practices для клиентов:

1. **Генерация nonce:**
   - Используйте криптографически стойкие генераторы
   - UUID v4, crypto.randomBytes(), или os.urandom()
   - Избегайте предсказуемых паттернов (timestamp + counter)

2. **Синхронизация времени:**
   - Используйте NTP для синхронизации часов
   - Учитывайте network latency при генерации timestamp
   - Мониторьте clock drift на серверах

3. **Обработка ошибок:**
   - Не ретраите 409 ошибки автоматически
   - Логируйте все replay detection инциденты
   - Реализуйте exponential backoff для других ошибок

4. **Мониторинг:**
   - Отслеживайте частоту 409 ошибок
   - Алертинг на аномальные паттерны replay-атак
   - Периодическая ротация API ключей

### ⚠️ Потенциальные проблемы:

#### **Clock Skew**
- **Проблема**: Разные часы на клиенте и сервере
- **Решение**: Мониторинг отклонения, настройка NTP

#### **Network Delays**
- **Проблема**: Запрос попадает на сервер после истечения временного окна
- **Решение**: Увеличение MAX_TIMESTAMP_AGE_SECONDS для медленных сетей

#### **Memory Leaks**
- **Проблема**: Бесконечный рост nonce кеша
- **Решение**: Регулярная очистка, мониторинг размера кеша

---

## 🆘 Troubleshooting

### 🔍 Диагностические команды:

#### **Проверка статистики защиты:**
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/security/replay-stats
```

#### **Проверка конфигурации:**
```bash
curl -H "X-API-Key: your-key" http://localhost:8000/api/v1/security/config
```

#### **Проверка логов:**
```bash
docker logs webhook-dispatcher | grep "🛡️"
```

### 📋 Частые проблемы и решения:

#### **❌ "Missing X-Timestamp header"**
```bash
# Проблема: Клиент не отправляет X-Timestamp
# Решение: Добавить заголовок с текущим timestamp

curl -H "X-Timestamp: $(date +%s)" ...
```

#### **❌ "Nonce too short"**
```bash  
# Проблема: X-Nonce менее 16 символов
# Решение: Использовать более длинный nonce

curl -H "X-Nonce: $(openssl rand -hex 16)" ...  # 32 символа
```

#### **❌ "Timestamp expired"**
```bash
# Проблема: Часы клиента отстают
# Решение: Синхронизация времени через NTP

sudo ntpdate -s time.nist.gov
```

#### **❌ "Replay attack detected"**
```bash
# Проблема: Повторное использование nonce
# Решение: Генерировать новый nonce для каждого запроса

# НЕ ДЕЛАЙТЕ ТАК:
NONCE="static-nonce-123"
curl -H "X-Nonce: $NONCE" ...
curl -H "X-Nonce: $NONCE" ...  # ❌ Replay!

# ДЕЛАЙТЕ ТАК:
curl -H "X-Nonce: $(uuidgen)" ...
curl -H "X-Nonce: $(uuidgen)" ...  # ✅ Уникальные nonce
```

---

## 🚀 Заключение

Защита от replay-атак в **Webhook Dispatcher** обеспечивает:

- 🛡️ **Полную защиту** от повторного воспроизведения перехваченных запросов
- ⚡ **Высокую производительность** с минимальными накладными расходами  
- 🔧 **Гибкую настройку** под различные требования безопасности
- 📊 **Подробный мониторинг** и статистику для операционной команды
- 🧪 **Comprehensive тестирование** всех сценариев атак

**Результат:** Ваша система теперь устойчива к одному из самых распространенных типов атак на webhook endpoints! 🎉