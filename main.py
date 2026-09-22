#!/usr/bin/env python3
"""
Entry Point для Secure B2B Webhook Dispatcher.

Этот файл служит точкой входа в приложение и импортирует основное приложение
из app пакета. Следует принципам Clean Architecture - минимальная логика,
только инициализация и запуск.
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем корневую папку проекта в Python path для корректных импортов
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Импортируем приложение из app пакета
try:
    from app.main import app
except ImportError as e:
    print(f"❌ Ошибка импорта приложения: {e}")
    print("💡 Убедитесь что все зависимости установлены: pip install -r requirements.txt")
    sys.exit(1)

# Настройка логирования для entry point
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    Главная функция для запуска приложения в режиме разработки.
    
    В production используйте uvicorn или gunicorn напрямую:
    - uvicorn app.main:app --host 0.0.0.0 --port 8000
    - gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
    """
    try:
        import uvicorn
        
        logger.info("🚀 Запуск Secure B2B Webhook Dispatcher...")
        logger.info("📁 Рабочая директория: %s", os.getcwd())
        logger.info("🐍 Python версия: %s", sys.version)
        logger.info("📦 Путь к приложению: app.main:app")
        
        # Параметры для development сервера
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,  # Автоперезагрузка при изменении файлов (только для development!)
            log_level="info",
            access_log=True,
            # reload_dirs=["app"],  # Отслеживать изменения только в app/
        )
        
    except KeyboardInterrupt:
        logger.info("👋 Приложение остановлено пользователем")
        
    except ImportError as e:
        logger.error("❌ Отсутствует uvicorn. Установите: pip install uvicorn[standard]")
        logger.error("📋 Или запустите через: python -m uvicorn app.main:app")
        sys.exit(1)
        
    except Exception as e:
        logger.error("❌ Критическая ошибка запуска: %s", e)
        sys.exit(1)


def check_environment():
    """
    Проверка окружения и зависимостей перед запуском.
    
    Returns:
        bool: True если окружение настроено корректно
    """
    checks = []
    
    # Проверка Python версии
    python_version = sys.version_info
    if python_version >= (3, 11):
        checks.append("✅ Python версия: OK")
    else:
        checks.append(f"❌ Python версия: {python_version} (требуется 3.11+)")
        return False
    
    # Проверка структуры проекта
    required_dirs = ["app", "data", "tests"]
    for dir_name in required_dirs:
        if (project_root / dir_name).exists():
            checks.append(f"✅ Директория {dir_name}/: OK")
        else:
            checks.append(f"❌ Директория {dir_name}/: Не найдена")
            return False
    
    # Проверка основных файлов
    required_files = [
        "app/__init__.py",
        "app/main.py", 
        "app/models.py",
        "app/schemas.py",
        "requirements.txt"
    ]
    for file_path in required_files:
        if (project_root / file_path).exists():
            checks.append(f"✅ Файл {file_path}: OK")
        else:
            checks.append(f"❌ Файл {file_path}: Не найден")
            return False
    
    # Проверка .env файла
    env_file = project_root / ".env"
    if env_file.exists():
        checks.append("✅ Файл .env: OK")
    else:
        checks.append("⚠️  Файл .env: Не найден (будут использованы значения по умолчанию)")
        checks.append("💡 Скопируйте .env.example в .env и настройте ключи")
    
    # Вывод результатов проверки
    print("\n" + "="*60)
    print("🔍 ПРОВЕРКА ОКРУЖЕНИЯ")
    print("="*60)
    for check in checks:
        print(check)
    print("="*60)
    
    return True


if __name__ == "__main__":
    """
    Запуск приложения из командной строки: python main.py
    
    Для production используйте:
    - Docker: docker-compose up
    - Uvicorn: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
    - Gunicorn: gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
    """
    
    # Проверяем окружение перед запуском
    if not check_environment():
        print("\n❌ Обнаружены проблемы с окружением. Исправьте их перед запуском.")
        sys.exit(1)
    
    print("\n🎯 Для production используйте Docker или uvicorn напрямую!")
    print("📖 Документация API будет доступна на: http://localhost:8000/docs")
    print("\n" + "="*60)
    
    # Запуск приложения
    main()