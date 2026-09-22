#!/usr/bin/env python3
"""
Тестовый скрипт для проверки генерации PDF отчётов
"""

import os
import sys
from pathlib import Path

# Добавляем путь к корневой директории проекта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.report_builder import ReportBuilder
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sample_report():
    """Тестирует генерацию отчёта с примерными данными"""
    try:
        # Создаём генератор отчётов
        builder = ReportBuilder()
        
        # Путь для сохранения тестового PDF
        output_path = Path("/tmp") / "sample_report.pdf"
        
        # Генерируем тестовый отчёт
        result_path = builder.generate_sample_report(
            client_name="ООО \"Тестовая Компания\"",
            output_path=str(output_path)
        )
        
        print(f"✅ Тестовый отчёт успешно создан: {result_path}")
        print(f"📄 Размер файла: {os.path.getsize(result_path)} байт")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при генерации тестового отчёта: {e}")
        return False

def test_excel_processing():
    """Тестирует обработку Excel файла (если есть)"""
    try:
        builder = ReportBuilder()
        
        # Создаём тестовый Excel файл
        import pandas as pd
        
        test_data = {
            'Дата': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'Канал': ['Google Ads', 'Facebook Ads', 'Organic Search', 'Email Marketing', 'Referral'],
            'Выручка': [25000, 18500, 12300, 9800, 14200],
            'Лиды': [8, 6, 4, 3, 5],
            'CTR': [2.5, 1.8, 3.2, 2.1, 1.9],
            'CPC': [85, 92, 0, 120, 0]
        }
        
        df = pd.DataFrame(test_data)
        excel_path = Path("/tmp") / "test_data.xlsx"
        df.to_excel(excel_path, index=False)
        
        # Генерируем отчёт из Excel
        pdf_path = Path("/tmp") / "excel_report.pdf"
        result_path = builder.process_excel_to_pdf(
            input_excel_path=str(excel_path),
            output_pdf_path=str(pdf_path),
            client_name="Excel Test Client"
        )
        
        print(f"✅ PDF отчёт из Excel успешно создан: {result_path}")
        print(f"📄 Размер файла: {os.path.getsize(result_path)} байт")
        
        # Удаляем тестовый Excel файл
        os.remove(excel_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при обработке Excel: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестирования генератора PDF отчётов...")
    print("-" * 50)
    
    success_count = 0
    total_tests = 2
    
    # Тест 1: Генерация с примерными данными
    print("\n1️⃣ Тестирование генерации отчёта с примерными данными...")
    if test_sample_report():
        success_count += 1
    
    # Тест 2: Обработка Excel файла
    print("\n2️⃣ Тестирование обработки Excel файла...")
    if test_excel_processing():
        success_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Результаты тестирования: {success_count}/{total_tests} тестов прошло успешно")
    
    if success_count == total_tests:
        print("✅ Все тесты пройдены! Система генерации отчётов готова к работе.")
    else:
        print("❌ Некоторые тесты не прошли. Проверьте зависимости и конфигурацию.")
        sys.exit(1)