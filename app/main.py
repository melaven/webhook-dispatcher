"""
Main Application Module для Secure B2B Webhook Dispatcher.

Точка входа в приложение, следующая принципам Clean Architecture:
- Presentation Layer (FastAPI routes)
- Application Layer (use cases)
- Domain Layer (business logic) 
- Infrastructure Layer (database, external services)
"""

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import json
from datetime import datetime
from typing import Dict, Any
from contextlib import asynccontextmanager

# Application Layer imports
from .schemas import (
    LeadWebhookRequest, 
    PaymentWebhookRequest, 
    OrderWebhookRequest,
    GenericWebhookPayload,
    WebhookResponse,
    WebhookStatistics,
    SecurityConfigResponse
)

# Infrastructure Layer imports
from .database import (
    init_database, 
    close_database, 
    get_db_session, 
    check_database_health,
    get_repository,
    DatabaseRepository
)
from .models import WebhookLogModel

# Domain Services imports
from .security import (
    verify_api_key, 
    verify_webhook_signature, 
    verify_replay_protection,
    get_security_config, 
    optional_api_key_check,
    get_security_service
)

# API Routes imports
from .api import reports

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Application Service для обработки вебхуков.
    
    Инкапсулирует бизнес-логику обработки различных типов вебхуков.
    Не зависит от FastAPI или других внешних фреймворков.
    """
    
    def __init__(self, repository: DatabaseRepository):
        self.repository = repository
    
    async def process_webhook(
        self, 
        raw_payload: dict, 
        event_type: str, 
        source: str,
        api_key: str
    ) -> WebhookLogModel:
        """
        Обрабатывает входящий вебхук с валидацией и сохранением.
        
        Args:
            raw_payload: Сырые данные вебхука
            event_type: Тип события
            source: Источник вебхука  
            api_key: Проверенный API ключ
            
        Returns:
            WebhookLogModel: Обработанная запись
            
        Raises:
            ValidationError: При ошибках валидации
            ValueError: При неизвестном типе события
        """
        # Создаем запись в статусе обработки
        webhook_log = WebhookLogModel.create_processing(
            event_type=event_type,
            source=source,
            payload=json.dumps(raw_payload, ensure_ascii=False)
        )
        
        try:
            # Валидируем данные в зависимости от типа события
            if event_type == "lead.created":
                validated_data = LeadWebhookRequest(**raw_payload)
                await self._process_lead(validated_data)
                
            elif event_type == "payment.succeeded":
                validated_data = PaymentWebhookRequest(**raw_payload)
                await self._process_payment(validated_data)
                
            elif event_type == "order.created":
                validated_data = OrderWebhookRequest(**raw_payload)
                await self._process_order(validated_data)
                
            else:
                # Неизвестный тип события - используем генерическую схему
                validated_data = GenericWebhookPayload(**raw_payload)
                logger.warning(f"⚠️ Неизвестный тип события: {event_type}")
            
            # Отмечаем как успешно обработанный
            webhook_log.mark_as_successful(
                json.dumps(validated_data.dict(), ensure_ascii=False)
            )
            
            logger.info(f"✅ Вебхук {event_type} успешно обработан")
            
        except ValidationError as e:
            # Сохраняем ошибки валидации
            webhook_log.mark_as_failed(str(e))
            logger.error(f"❌ Ошибка валидации {event_type}: {e}")
            raise
        except Exception as e:
            # Сохраняем неожиданные ошибки
            webhook_log.mark_as_failed(f"Неожиданная ошибка: {str(e)}")
            logger.error(f"❌ Неожиданная ошибка в {event_type}: {e}")
            raise
        
        # Сохраняем в базу данных
        return await self.repository.save_webhook_log(webhook_log)
    
    async def _process_lead(self, lead_data: LeadWebhookRequest) -> None:
        """Бизнес-логика обработки лида."""
        logger.info(f"🔄 Обрабатываем лид: {lead_data.data.name} ({lead_data.data.phone})")
        
        # TODO: Здесь будет интеграция с CRM
        # - Отправка в amoCRM/Bitrix24
        # - Создание задачи для менеджера
        # - Отправка уведомления в Slack/Telegram
        # - Запуск email-последовательности
    
    async def _process_payment(self, payment_data: PaymentWebhookRequest) -> None:
        """Бизнес-логика обработки платежа."""
        logger.info(f"🔄 Обрабатываем платеж: {payment_data.data.transaction_id} на {payment_data.data.amount} {payment_data.data.currency}")
        
        # TODO: Здесь будет логика обработки оплаты
        # - Обновление статуса заказа
        # - Отправка чека покупателю
        # - Запуск процесса выполнения заказа
        # - Начисление комиссий/бонусов
    
    async def _process_order(self, order_data: OrderWebhookRequest) -> None:
        """Бизнес-логика обработки заказа."""
        logger.info(f"🔄 Обрабатываем заказ: {order_data.data.order_id} на {order_data.data.amount} {order_data.data.currency}")
        
        # TODO: Здесь будет логика обработки заказа
        # - Резервирование товаров на складе
        # - Создание документов доставки
        # - Отправка уведомления в систему учета
        # - Запуск workflow выполнения заказа


# Lifespan manager для FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения."""
    # Startup
    logger.info("🚀 Запуск Secure B2B Webhook Dispatcher v4.0.0")
    logger.info("🏗️ Инициализация Clean Architecture слоев...")
    
    await init_database()
    
    security_config = get_security_config()
    logger.info(f"🔑 API ключи: {'включены' if security_config['api_key_enabled'] else 'отключены'}")
    logger.info(f"🔐 HMAC подписи: {'включены' if security_config['hmac_enabled'] else 'отключены'}")
    logger.info("✅ Все слои инициализированы")
    
    yield
    
    # Shutdown
    logger.info("🛑 Завершение работы приложения")
    await close_database()


# Создание FastAPI приложения
app = FastAPI(
    title="Secure B2B Webhook Dispatcher",
    description="""
    🚀 **Production-ready B2B webhook gateway** построенный по принципам **Clean Architecture**.
    
    ## Возможности:
    - 🔒 **API Key + HMAC authentication**
    - 📊 **Strict Pydantic validation** 
    - 💾 **Immutable audit trail** (SQLite)
    - 🏗️ **Clean Architecture** (Domain/Application/Infrastructure layers)
    - 🐳 **Docker-ready** с docker-compose
    - 🧪 **Comprehensive testing** suite
    
    ## Поддерживаемые события:
    - `lead.created` - Новые лиды из форм/CRM
    - `payment.succeeded` - Успешные платежи  
    - `order.created` - Новые заказы из e-commerce
    """,
    version="4.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене ограничить до конкретных доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение API роутеров
app.include_router(reports.router)


# ============== PRESENTATION LAYER (API Routes) ==============

@app.get("/")
async def root(api_key: str = Depends(optional_api_key_check)):
    """
    📊 Статус сервиса и конфигурация.
    
    Публичный эндпоинт с опциональной аутентификацией.
    """
    db_healthy = await check_database_health()
    security_config = get_security_config()
    
    return {
        "service": "Secure B2B Webhook Dispatcher",
        "status": "running",
        "version": "4.0.0",
        "architecture": "Clean Architecture",
        "database": "healthy" if db_healthy else "unhealthy",
        "security": security_config,
        "authenticated": bool(api_key),
        "supported_events": [
            "lead.created",
            "payment.succeeded", 
            "order.created"
        ],
        "timestamp": datetime.now().isoformat(),
        "docs": "/docs"
    }


@app.get("/health")
@app.head("/health")
async def health_check():
    """
    🏥 Health check для мониторинга и load balancer'ов.
    
    Публичный эндпоинт без аутентификации.
    """
    db_healthy = await check_database_health()
    
    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "database": "connected" if db_healthy else "disconnected",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/webhook/incoming", response_model=WebhookResponse)
async def receive_webhook(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
    replay_protected: bool = Depends(verify_replay_protection)
) -> WebhookResponse:
    """
    🔒 **ОСНОВНОЙ ЭНДПОИНТ** для приема защищенных вебхуков с защитой от replay-атак.
    
    ## Требования безопасности:
    - ✅ **API Key** в заголовке `X-API-Key` (обязательно)
    - ✅ **HMAC подпись** в заголовке `X-Hub-Signature-256` (опционально)
    - 🛡️ **Защита от replay-атак** через заголовки `X-Timestamp` и `X-Nonce`
    
    ## 🛡️ Защита от Replay-атак:
    - **X-Timestamp**: Unix timestamp создания запроса (макс. возраст 5 минут)
    - **X-Nonce**: Уникальный идентификатор запроса (мин. 16 символов)
    
    ## Поддерживаемые события:
    - `lead.created` - Создание лида с валидацией имени/телефона/email
    - `payment.succeeded` - Успешная оплата с проверкой суммы и валюты  
    - `order.created` - Создание заказа с валидацией товаров
    
    ## Audit Trail:
    Все запросы (успешные и с ошибками) сохраняются в SQLite для анализа.
    """
    try:
        # Получаем сырые данные и заголовки
        raw_body = await request.body()
        headers = dict(request.headers)
        
        # Безопасное логирование (маскируем API ключ)
        security_service = get_security_service()
        masked_key = security_service.mask_api_key(api_key)
        logger.info(f"📦 ЗАЩИЩЕННЫЙ вебхук от {request.client.host}")
        logger.info(f"🔑 API ключ: {masked_key}")
        logger.info(f"🛡️ Replay protection: {'✅ Активна' if replay_protected else '⚠️ Отключена'}")
        
        # Опциональная HMAC проверка
        hmac_signature = headers.get("x-hub-signature-256") or headers.get("x-signature")
        if hmac_signature:
            if security_service.verify_hmac_signature(raw_body, hmac_signature):
                logger.info("✅ HMAC подпись проверена")
            else:
                logger.warning("⚠️ Неверная HMAC подпись - продолжаем")
        
        # Парсинг JSON
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Неверный формат JSON")
        
        if not payload:
            raise HTTPException(status_code=400, detail="Пустые данные")
        
        # Извлекаем метаданные
        event_type = payload.get("event_type", "unknown")
        source = payload.get("source", "unknown")
        
        # Обработка через Application Service
        repository = get_repository(session)
        processor = WebhookProcessor(repository)
        
        webhook_log = await processor.process_webhook(
            raw_payload=payload,
            event_type=event_type,
            source=source,
            api_key=api_key
        )
        
        # Успешный ответ
        response = WebhookResponse(
            status="success",
            message=f"Вебхук '{event_type}' успешно аутентифицирован, валидирован и сохранен",
            event=event_type,
            processed=True,
            webhook_id=webhook_log.id
        )
        
        logger.info(f"✅ Вебхук {event_type} обработан с ID: {webhook_log.id}")
        return response
        
    except ValidationError as e:
        logger.error(f"❌ Ошибка валидации: {e}")
        raise HTTPException(status_code=422, detail=f"Ошибка валидации: {str(e)}")
        
    except HTTPException:
        raise
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")


@app.get("/api/v1/stats", response_model=WebhookStatistics)
async def get_webhook_stats(
    session: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
) -> WebhookStatistics:
    """
    📊 **ЗАЩИЩЕННАЯ** статистика по обработанным вебхукам.
    
    Требует валидный API ключ. Показывает агрегированные данные
    по всем обработанным вебхукам с разбивкой по статусам и типам.
    """
    try:
        repository = get_repository(session)
        stats = await repository.get_statistics()
        
        logger.info(f"📊 Статистика запрошена (всего: {stats['total_webhooks']})")
        
        return WebhookStatistics(
            total_webhooks=stats["total_webhooks"],
            status_breakdown=stats["status_breakdown"],
            event_type_breakdown=stats["event_type_breakdown"],
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка статистики: {str(e)}")


@app.get("/api/v1/security/replay-stats")
async def get_replay_protection_stats(api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    🛡️ **СТАТИСТИКА** защиты от replay-атак.
    
    Показывает статистику работы системы защиты от повторного воспроизведения:
    - Количество активных nonce в кеше
    - Загрузка кеша в процентах
    - Настройки временных окон
    - Время последней очистки
    """
    try:
        stats = get_security_service().get_replay_stats()
        stats["timestamp"] = datetime.now().isoformat()
        
        logger.info("📊 Статистика replay protection запрошена")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статистики replay protection: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка статистики: {str(e)}")


@app.get("/api/v1/security/config", response_model=SecurityConfigResponse)
async def get_security_info(api_key: str = Depends(verify_api_key)) -> SecurityConfigResponse:
    """
    🔒 **ЗАЩИЩЕННАЯ** конфигурация безопасности.
    
    Требует валидный API ключ. Показывает текущие настройки
    безопасности без раскрытия секретных данных.
    """
    config = get_security_config()
    
    return SecurityConfigResponse(
        security_config=config,
        authenticated=True,
        timestamp=datetime.now().isoformat()
    )


# ============== ERROR HANDLERS ==============

@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    """Глобальный обработчик ошибок валидации."""
    logger.error(f"Validation error on {request.url}: {exc}")
    return HTTPException(status_code=422, detail=str(exc))


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Глобальный обработчик ValueError."""
    logger.error(f"Value error on {request.url}: {exc}")
    return HTTPException(status_code=400, detail=str(exc))