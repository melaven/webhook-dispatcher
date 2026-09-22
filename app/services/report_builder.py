import pandas as pd
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ReportBuilder:
    def __init__(self, template_dir="templates"):
        """
        Инициализация генератора отчётов
        
        Args:
            template_dir: Путь к директории с HTML шаблонами
        """
        # Определяем абсолютный путь к шаблонам
        if not os.path.isabs(template_dir):
            # Если путь относительный, строим от корня проекта
            project_root = Path(__file__).parent.parent.parent
            template_path = project_root / template_dir
        else:
            template_path = Path(template_dir)
            
        if not template_path.exists():
            raise FileNotFoundError(f"Директория шаблонов не найдена: {template_path}")
            
        # Подключаем Jinja2 к папке с шаблонами
        self.env = Environment(loader=FileSystemLoader(str(template_path)))
        self.template = self.env.get_template("report_template.html")

    def process_excel_to_pdf(self, input_excel_path: str, output_pdf_path: str, client_name: str) -> str:
        """
        Обрабатывает Excel файл и генерирует PDF отчёт
        
        Args:
            input_excel_path: Путь к входному Excel файлу
            output_pdf_path: Путь для сохранения PDF
            client_name: Имя клиента для отчёта
            
        Returns:
            Путь к сгенерированному PDF файлу
            
        Raises:
            FileNotFoundError: Если Excel файл не найден
            Exception: При ошибках генерации отчёта
        """
        try:
            # 1. Проверяем существование входного файла
            if not os.path.exists(input_excel_path):
                raise FileNotFoundError(f"Excel файл не найден: {input_excel_path}")
            
            # 2. Читаем Excel файл
            logger.info(f"Чтение Excel файла: {input_excel_path}")
            df = pd.read_excel(input_excel_path)
            
            if df.empty:
                logger.warning("Excel файл пуст, генерируем отчёт с нулевыми метриками")

            # 3. Агрегируем бизнес-метрики (названия колонок зависят от шаблона)
            # Используем .get() или проверяем наличие, чтобы не падало на кривых файлах
            revenue = self._calculate_revenue(df)
            leads = self._calculate_leads(df)
            conversion = self._calculate_conversion(df, leads)

            # 4. Превращаем топ-10 строк датафрейма в HTML-таблицу для отчета
            html_table = self._generate_html_table(df)

            # 5. Собираем переменные для шаблона
            context = {
                "client_name": client_name,
                "date": datetime.now().strftime("%d.%m.%Y"),
                "total_revenue": f"{revenue:,.0f} ₽".replace(',', ' '),
                "total_leads": leads,
                "conversion_rate": conversion,
                "data_table": html_table
            }

            # Рендерим HTML и собираем PDF
            logger.info(f"Генерация PDF отчёта для клиента: {client_name}")
            rendered_html = self.template.render(**context)
            
            # Создаём директорию для PDF если не существует
            output_dir = Path(output_pdf_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Используем правильный API WeasyPrint
            html_doc = HTML(string=rendered_html)
            html_doc.write_pdf(output_pdf_path)
            
            logger.info(f"PDF успешно сгенерирован: {output_pdf_path}")
            return output_pdf_path

        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {str(e)}")
            raise

    def _calculate_revenue(self, df: pd.DataFrame) -> float:
        """Рассчитывает общую выручку из DataFrame"""
        revenue_columns = ['Выручка', 'Revenue', 'Сумма', 'Amount', 'Доход']
        
        for col in revenue_columns:
            if col in df.columns:
                try:
                    # Пробуем суммировать числовые значения
                    return pd.to_numeric(df[col], errors='coerce').fillna(0).sum()
                except Exception:
                    continue
        
        # Если не нашли подходящую колонку, возвращаем 0
        return 0.0

    def _calculate_leads(self, df: pd.DataFrame) -> int:
        """Рассчитывает количество лидов"""
        leads_columns = ['Лиды', 'Leads', 'Количество', 'Count', 'Клиенты']
        
        for col in leads_columns:
            if col in df.columns:
                try:
                    return int(pd.to_numeric(df[col], errors='coerce').fillna(0).sum())
                except Exception:
                    continue
        
        # Если не нашли колонку с лидами, считаем количество строк
        return len(df)

    def _calculate_conversion(self, df: pd.DataFrame, leads: int) -> float:
        """Рассчитывает конверсию в процентах"""
        if len(df) == 0:
            return 0.0
        
        # Простая конверсия: лиды / общее количество записей * 100
        conversion = round((leads / len(df)) * 100, 1) if len(df) > 0 else 0
        
        # Ограничиваем конверсию 100%
        return min(conversion, 100.0)

    def _generate_html_table(self, df: pd.DataFrame) -> str:
        """Генерирует HTML таблицу из DataFrame"""
        if df.empty:
            return "<p>Данные отсутствуют</p>"
        
        # Берём первые 10 строк для отчёта
        display_df = df.head(10)
        
        # Генерируем HTML таблицу без индекса
        html_table = display_df.to_html(
            index=False, 
            border=0, 
            classes="data-table",
            escape=False,
            table_id="report-table"
        )
        
        return html_table

    def generate_sample_report(self, client_name: str = "Тестовый Клиент", output_path: str = "sample_report.pdf") -> str:
        """
        Генерирует тестовый отчёт с примерными данными
        
        Args:
            client_name: Имя клиента
            output_path: Путь для сохранения PDF
            
        Returns:
            Путь к сгенерированному файлу
        """
        # Создаём тестовые данные
        sample_data = {
            'Дата': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19'],
            'Источник': ['Google Ads', 'Facebook', 'Organic', 'Email', 'Referral'],
            'Выручка': [15000, 22500, 8900, 12400, 19600],
            'Лиды': [5, 8, 3, 4, 7],
            'Конверсия': [2.1, 3.2, 1.8, 2.5, 2.9]
        }
        
        df = pd.DataFrame(sample_data)
        
        # Рассчитываем метрики
        revenue = df['Выручка'].sum()
        leads = df['Лиды'].sum()
        conversion = round((leads / len(df)) * 100 / 10, 1)  # Нормализуем конверсию
        
        # Генерируем HTML таблицу
        html_table = self._generate_html_table(df)
        
        # Контекст для шаблона
        context = {
            "client_name": client_name,
            "date": datetime.now().strftime("%d.%m.%Y"),
            "total_revenue": f"{revenue:,.0f} ₽".replace(',', ' '),
            "total_leads": leads,
            "conversion_rate": conversion,
            "data_table": html_table
        }
        
        # Рендерим и сохраняем
        rendered_html = self.template.render(**context)
        html_doc = HTML(string=rendered_html)
        html_doc.write_pdf(output_path)
        
        logger.info(f"Тестовый PDF отчёт сгенерирован: {output_path}")
        return output_path