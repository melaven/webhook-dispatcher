"""
Security Service для Webhook Dispatcher.

Инкапсулирует всю логику безопасности: API ключи, HMAC подписи, аутентификацию,
и защиту от replay-атак. Следует принципам Clean Architecture.
"""

import hmac
import hashlib
import os
import time
from typing import Optional, Dict, Any, Set
from fastapi import HTTPException, Security, Header
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv
import logging
from dataclasses import dataclass
from threading import Lock
from collections import defaultdict

logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()


@dataclass(frozen=True)
class SecurityConfig:
    """
    Value Object для конфигурации безопасности.
    
    Immutable объект, который содержит всю конфигурацию безопасности.
    Следует принципам DDD - не содержит бизнес-логики, только данные.
    """
    api_key: str
    hmac_secret: str
    api_key_source: str
    hmac_source: str
    
    # Защита от replay-атак
    replay_protection_enabled: bool = True
    max_timestamp_age_seconds: int = 300  # 5 минут
    nonce_cache_size: int = 10000
    nonce_cleanup_interval: int = 3600  # 1 час
    
    @property
    def api_key_enabled(self) -> bool:
        """Проверка что API ключи включены."""
        return bool(self.api_key)
    
    @property
    def hmac_enabled(self) -> bool:
        """Проверка что HMAC подписи включены."""
        return bool(self.hmac_secret)
    
    def to_dict(self) -> Dict[str, Any]:
        """Безопасное представление конфигурации для API."""
        return {
            "api_key_enabled": self.api_key_enabled,
            "hmac_enabled": self.hmac_enabled,
            "api_key_source": self.api_key_source,
            "hmac_source": self.hmac_source,
            "replay_protection_enabled": self.replay_protection_enabled,
            "max_timestamp_age_seconds": self.max_timestamp_age_seconds,
            "nonce_cache_size": self.nonce_cache_size
        }


class ReplayProtectionCache:
    """
    Thread-safe кеш для защиты от replay-атак.
    
    Хранит использованные nonce и очищает устаревшие записи.
    """
    
    def __init__(self, max_size: int = 10000, cleanup_interval: int = 3600):
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self._nonces: Set[str] = set()
        self._nonce_timestamps: Dict[str, float] = {}
        self._lock = Lock()
        self._last_cleanup = time.time()
    
    def is_nonce_used(self, nonce: str) -> bool:
        """
        Проверяет был ли nonce уже использован.
        
        Args:
            nonce: Уникальный идентификатор запроса
            
        Returns:
            bool: True если nonce уже использовался
        """
        with self._lock:
            return nonce in self._nonces
    
    def add_nonce(self, nonce: str) -> bool:
        """
        Добавляет nonce в кеш.
        
        Args:
            nonce: Уникальный идентификатор запроса
            
        Returns:
            bool: True если nonce был добавлен, False если уже существовал
        """
        with self._lock:
            if nonce in self._nonces:
                return False
            
            current_time = time.time()
            
            # Добавляем новый nonce
            self._nonces.add(nonce)
            self._nonce_timestamps[nonce] = current_time
            
            # Периодическая очистка
            if current_time - self._last_cleanup > self.cleanup_interval:
                self._cleanup_expired_nonces()
            
            # Ограничиваем размер кеша
            if len(self._nonces) > self.max_size:
                self._remove_oldest_nonces()
            
            return True
    
    def _cleanup_expired_nonces(self):
        """Удаляет устаревшие nonce из кеша."""
        current_time = time.time()
        expired_nonces = [
            nonce for nonce, timestamp in self._nonce_timestamps.items()
            if current_time - timestamp > 3600  # 1 час
        ]
        
        for nonce in expired_nonces:
            self._nonces.discard(nonce)
            self._nonce_timestamps.pop(nonce, None)
        
        self._last_cleanup = current_time
        
        if expired_nonces:
            logger.info(f"🧹 Очищено {len(expired_nonces)} устаревших nonce")
    
    def _remove_oldest_nonces(self):
        """Удаляет самые старые nonce при превышении лимита."""
        if len(self._nonces) <= self.max_size:
            return
            
        sorted_nonces = sorted(
            self._nonce_timestamps.items(), 
            key=lambda x: x[1]
        )
        
        # Удаляем лишние записи до достижения max_size
        excess_count = len(sorted_nonces) - self.max_size
        if excess_count > 0:
            for nonce, _ in sorted_nonces[:excess_count]:
                self._nonces.discard(nonce)
                self._nonce_timestamps.pop(nonce, None)
            
            logger.info(f"🗑️ Удалено {excess_count} старых nonce (превышен лимит)")
        
        # Дополнительно удаляем еще 10% для создания буфера
        buffer_count = max(1, self.max_size // 10)
        if len(sorted_nonces) > excess_count:
            for nonce, _ in sorted_nonces[excess_count:excess_count + buffer_count]:
                if nonce in self._nonces:  # Проверяем что еще не удален
                    self._nonces.discard(nonce)
                    self._nonce_timestamps.pop(nonce, None)
            
            if buffer_count > 0:
                logger.info(f"🗑️ Удалено дополнительно {buffer_count} nonce (создание буфера)")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику кеша."""
        with self._lock:
            return {
                "total_nonces": len(self._nonces),
                "max_size": self.max_size,
                "cache_usage_percent": (len(self._nonces) / self.max_size) * 100,
                "last_cleanup": self._last_cleanup
            }


class SecurityService:
    """
    Доменный сервис для работы с безопасностью.
    
    Инкапсулирует всю логику аутентификации, авторизации и защиты от replay-атак.
    Не зависит от FastAPI или других внешних фреймворков.
    """
    
    def __init__(self, config: SecurityConfig):
        self.config = config
        self.replay_cache = ReplayProtectionCache(
            max_size=config.nonce_cache_size,
            cleanup_interval=config.nonce_cleanup_interval
        ) if config.replay_protection_enabled else None
    
    def verify_api_key(self, provided_key: Optional[str]) -> bool:
        """
        Проверяет корректность предоставленного API ключа.
        
        Args:
            provided_key: Ключ от клиента
            
        Returns:
            bool: True если ключ валидный
        """
        if not provided_key:
            logger.warning("🚫 Попытка доступа без API ключа")
            return False
        
        if not self.config.api_key_enabled:
            logger.warning("🚫 API ключи отключены в конфигурации")
            return False
        
        is_valid = hmac.compare_digest(provided_key, self.config.api_key)
        
        if is_valid:
            logger.info("✅ API ключ успешно проверен")
        else:
            logger.warning(f"🚫 Неверный API ключ: {provided_key[:10]}...")
        
        return is_valid
    
    def verify_hmac_signature(self, payload_body: bytes, received_signature: str) -> bool:
        """
        Проверяет HMAC-SHA256 подпись вебхука.
        
        Args:
            payload_body: Сырое тело запроса
            received_signature: Подпись из заголовка
            
        Returns:
            bool: True если подпись валидна
        """
        if not self.config.hmac_enabled:
            logger.info("ℹ️ HMAC проверка отключена")
            return True
        
        if not received_signature:
            logger.warning("⚠️ Отсутствует HMAC подпись")
            return False
        
        # Убираем префикс "sha256=" если он есть
        signature = received_signature
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        # Вычисляем ожидаемую подпись
        computed_signature = hmac.new(
            self.config.hmac_secret.encode("utf-8"),
            payload_body,
            hashlib.sha256
        ).hexdigest()
        
        # Защита от timing-attacks
        is_valid = hmac.compare_digest(computed_signature, signature)
        
        if is_valid:
            logger.info("✅ HMAC подпись валидна")
        else:
            logger.warning(f"🚫 Неверная HMAC подпись. Ожидали: {computed_signature[:10]}..., получили: {signature[:10]}...")
        
        return is_valid
    
    def verify_timestamp(self, timestamp: Optional[str]) -> bool:
        """
        🛡️ ЗАЩИТА ОТ REPLAY-АТАК: Проверяет актуальность timestamp запроса.
        
        Отклоняет запросы старше max_timestamp_age_seconds для предотвращения
        повторного воспроизведения перехваченных запросов.
        
        Args:
            timestamp: Unix timestamp из заголовка X-Timestamp
            
        Returns:
            bool: True если timestamp в допустимых пределах
        """
        if not self.config.replay_protection_enabled:
            logger.info("ℹ️ Защита от replay-атак отключена")
            return True
        
        if not timestamp:
            logger.warning("🛡️ Отсутствует заголовок X-Timestamp - возможная replay-атака")
            return False
        
        try:
            request_time = float(timestamp)
            current_time = time.time()
            age_seconds = current_time - request_time
            
            # Проверяем что запрос не из будущего (допускаем погрешность 60 секунд)
            if request_time > current_time + 60:
                logger.warning(f"🛡️ Timestamp из будущего: {age_seconds:.2f}s - отклоняем")
                return False
            
            # Проверяем что запрос не слишком старый
            if age_seconds > self.config.max_timestamp_age_seconds:
                logger.warning(f"🛡️ Устаревший timestamp: {age_seconds:.2f}s > {self.config.max_timestamp_age_seconds}s - возможная replay-атака")
                return False
            
            logger.info(f"✅ Timestamp валиден (возраст: {age_seconds:.2f}s)")
            return True
            
        except (ValueError, TypeError) as e:
            logger.warning(f"🛡️ Неверный формат timestamp '{timestamp}': {e}")
            return False
    
    def verify_nonce(self, nonce: Optional[str]) -> bool:
        """
        🛡️ ЗАЩИТА ОТ REPLAY-АТАК: Проверяет уникальность nonce.
        
        Каждый запрос должен иметь уникальный nonce для предотвращения
        повторного воспроизведения одного и того же запроса.
        
        Args:
            nonce: Уникальный идентификатор из заголовка X-Nonce
            
        Returns:
            bool: True если nonce уникален и не использовался ранее
        """
        if not self.config.replay_protection_enabled or not self.replay_cache:
            logger.info("ℹ️ Проверка nonce отключена")
            return True
        
        if not nonce:
            logger.warning("🛡️ Отсутствует заголовок X-Nonce - возможная replay-атака")
            return False
        
        # Проверяем длину nonce (должен быть достаточно длинным)
        if len(nonce) < 16:
            logger.warning(f"🛡️ Nonce слишком короткий: {len(nonce)} символов (минимум 16)")
            return False
        
        # Проверяем был ли nonce уже использован
        if self.replay_cache.is_nonce_used(nonce):
            logger.warning(f"🛡️ REPLAY-АТАКА ОБНАРУЖЕНА! Nonce уже использовался: {nonce[:16]}...")
            return False
        
        # Добавляем nonce в кеш
        if not self.replay_cache.add_nonce(nonce):
            logger.error(f"🛡️ Не удалось добавить nonce в кеш: {nonce[:16]}...")
            return False
        
        logger.info(f"✅ Nonce уникален и добавлен в кеш: {nonce[:16]}...")
        return True
    
    def verify_replay_protection(self, timestamp: Optional[str], nonce: Optional[str]) -> bool:
        """
        🛡️ КОМПЛЕКСНАЯ ЗАЩИТА ОТ REPLAY-АТАК.
        
        Проверяет и timestamp и nonce для максимальной защиты от 
        повторного воспроизведения перехваченных запросов.
        
        Args:
            timestamp: Unix timestamp из заголовка X-Timestamp  
            nonce: Уникальный идентификатор из заголовка X-Nonce
            
        Returns:
            bool: True если запрос защищен от replay-атак
        """
        if not self.config.replay_protection_enabled:
            logger.info("ℹ️ Защита от replay-атак отключена")
            return True
        
        # Проверяем timestamp
        if not self.verify_timestamp(timestamp):
            return False
        
        # Проверяем nonce
        if not self.verify_nonce(nonce):
            return False
        
        logger.info("🛡️ Запрос прошел полную защиту от replay-атак")
        return True
    
    def get_replay_stats(self) -> Dict[str, Any]:
        """Возвращает статистику защиты от replay-атак."""
        if not self.replay_cache:
            return {"replay_protection_enabled": False}
        
        stats = self.replay_cache.get_stats()
        stats["replay_protection_enabled"] = True
        stats["max_timestamp_age_seconds"] = self.config.max_timestamp_age_seconds
        return stats
    
    def mask_api_key(self, api_key: str) -> str:
        """
        Маскирует API ключ для безопасного логирования.
        
        Args:
            api_key: Полный API ключ
            
        Returns:
            str: Замаскированный ключ
        """
        if len(api_key) <= 8:
            return "***"
        return f"{api_key[:8]}..."


# Глобальный экземпляр конфигурации
_security_config = SecurityConfig(
    api_key=os.getenv("DISPATCHER_API_KEY", "test-secret-key-12345"),
    hmac_secret=os.getenv("WEBHOOK_SECRET", "super-secret-hmac-key"),
    api_key_source="environment" if os.getenv("DISPATCHER_API_KEY") else "default",
    hmac_source="environment" if os.getenv("WEBHOOK_SECRET") else "default",
    # Настройки защиты от replay-атак
    replay_protection_enabled=os.getenv("REPLAY_PROTECTION_ENABLED", "true").lower() == "true",
    max_timestamp_age_seconds=int(os.getenv("MAX_TIMESTAMP_AGE_SECONDS", "300")),  # 5 минут
    nonce_cache_size=int(os.getenv("NONCE_CACHE_SIZE", "10000")),
    nonce_cleanup_interval=int(os.getenv("NONCE_CLEANUP_INTERVAL", "3600"))  # 1 час
)

# Глобальный экземпляр сервиса безопасности (ленивая инициализация)
security_service = None

def get_security_service():
    """Ленивая инициализация SecurityService."""
    global security_service
    if security_service is None:
        security_service = SecurityService(_security_config)
    return security_service

# FastAPI dependencies
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    FastAPI dependency для проверки API ключа.
    
    Args:
        api_key: API ключ из заголовка X-API-Key
        
    Returns:
        str: Валидный API ключ
        
    Raises:
        HTTPException: 403 если ключ неверный или отсутствует
    """
    if not api_key:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Missing API Key in X-API-Key header"
        )
    
    if not get_security_service().verify_api_key(api_key):
        raise HTTPException(
            status_code=403,
            detail="Access denied: Invalid API Key"
        )
    
    return api_key


async def optional_api_key_check(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    FastAPI dependency для опциональной проверки API ключа.
    
    Args:
        api_key: API ключ из заголовка X-API-Key
        
    Returns:
        Optional[str]: Валидный API ключ или None
    """
    if not api_key:
        logger.info("ℹ️ Запрос без API ключа (опциональная проверка)")
        return None
    
    if not get_security_service().verify_api_key(api_key):
        logger.warning(f"🚫 Неверный API ключ в опциональной проверке")
        return None
    
    return api_key


async def verify_webhook_signature(
    request_body: bytes,
    signature: Optional[str] = Header(None, alias="X-Hub-Signature-256")
) -> bool:
    """
    FastAPI dependency для проверки HMAC подписи вебхука.
    
    Args:
        request_body: Тело запроса в байтах
        signature: HMAC подпись из заголовка
        
    Returns:
        bool: True если подпись валидна
        
    Raises:
        HTTPException: 401 если подпись неверная или отсутствует
    """
    if not signature:
        logger.warning("🚫 Отсутствует заголовок с подписью")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Missing webhook signature"
        )
    
    if not get_security_service().verify_hmac_signature(request_body, signature):
        logger.error("🚫 Неверная подпись вебхука - возможная попытка подделки данных")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized: Invalid webhook signature"
        )
    
    return True


async def verify_replay_protection(
    timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
    nonce: Optional[str] = Header(None, alias="X-Nonce")
) -> bool:
    """
    🛡️ FastAPI dependency для защиты от replay-атак.
    
    Проверяет timestamp и nonce для предотвращения повторного воспроизведения
    перехваченных запросов.
    
    Args:
        timestamp: Unix timestamp из заголовка X-Timestamp
        nonce: Уникальный идентификатор из заголовка X-Nonce
        
    Returns:
        bool: True если запрос защищен от replay-атак
        
    Raises:
        HTTPException: 409 если обнаружена replay-атака
    """
    if not get_security_service().verify_replay_protection(timestamp, nonce):
        logger.error("🛡️ REPLAY-АТАКА ЗАБЛОКИРОВАНА!")
        raise HTTPException(
            status_code=409,  # Conflict - запрос уже был обработан
            detail="Replay attack detected: Request already processed or expired"
        )
    
    return True


def get_security_config() -> Dict[str, Any]:
    """
    Получает текущую конфигурацию безопасности.
    
    Returns:
        dict: Безопасное представление конфигурации
    """
    config_dict = _security_config.to_dict()
    config_dict.update(get_security_service().get_replay_stats())
    return config_dict


# Экспорт для обратной совместимости
MASTER_API_KEY = _security_config.api_key
WEBHOOK_SECRET = _security_config.hmac_secret