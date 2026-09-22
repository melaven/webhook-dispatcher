"""
Secure B2B Webhook Dispatcher - Application Package.

A high-performance, secure webhook gateway for B2B integrations with Clean Architecture.
"""

__version__ = "4.0.0"
__author__ = "webhook-dispatcher"
__description__ = "Production-ready B2B Webhook Gateway with FastAPI & Clean Architecture"

# Экспортируем основные компоненты для удобного импорта
from .main import app

__all__ = ["app"]