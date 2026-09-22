"""
API эндпоинты для генерации PDF отчётов
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends
from fastapi.responses import FileResponse
import tempfile
import os
import logging
from pathlib import Path
from typing import Optional

from app.services.report_builder import ReportBuilder
from app.security import verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reports", tags=["reports"])

# Инициализируем генератор отчётов
report_builder = ReportBuilder()


@router.post("/generate")
async def generate_pdf_report(
    excel_file: UploadFile = File(..., description="Excel файл с данными для отчёта"),
    client_name: str = Form(..., description="Имя клиента для отчёта", example="ООО \"Рога и Копыта\""),
    api_key: str = Depends(verify_api_key)
):
    """
    Генерирует PDF отчёт из загруженного Excel файла
    
    - **excel_file**: Excel файл (.xlsx, .xls) с данными
    - **client_name**: Название клиента для заголовка отчёта
    
    Возвращает сгенерированный PDF файл
    """
    
    # Проверяем формат файла
    if not excel_file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Поддерживаются только Excel файлы (.xlsx, .xls)"
        )
    
    # Проверяем размер файла (максимум 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if excel_file.size and excel_file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл слишком большой. Максимальный размер: {max_size // 1024 // 1024}MB"
        )
    
    temp_excel_path = None
    temp_pdf_path = None
    
    try:
        # Создаём временные файлы
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_excel:
            temp_excel_path = temp_excel.name
            # Читаем и сохраняем загруженный Excel файл
            content = await excel_file.read()
            temp_excel.write(content)
        
        # Создаём временный файл для PDF
        temp_pdf_fd, temp_pdf_path = tempfile.mkstemp(suffix='.pdf')
        os.close(temp_pdf_fd)  # Закрываем файловый дескриптор
        
        # Генерируем PDF отчёт
        logger.info(f"Генерация отчёта для клиента: {client_name}")
        result_path = report_builder.process_excel_to_pdf(
            input_excel_path=temp_excel_path,
            output_pdf_path=temp_pdf_path,
            client_name=client_name
        )
        
        # Формируем имя файла для скачивания
        safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"Отчёт_{safe_client_name}_{Path(temp_pdf_path).stem}.pdf"
        
        # Возвращаем PDF файл
        return FileResponse(
            path=result_path,
            filename=filename,
            media_type="application/pdf",
            background=_cleanup_temp_files(temp_excel_path, temp_pdf_path)
        )
        
    except Exception as e:
        # Очищаем временные файлы в случае ошибки
        _cleanup_temp_files_sync(temp_excel_path, temp_pdf_path)
        
        logger.error(f"Ошибка при генерации отчёта: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации отчёта: {str(e)}"
        )


@router.get("/sample")
async def generate_sample_report(
    client_name: str = "Демо Клиент",
    api_key: str = Depends(verify_api_key)
):
    """
    Генерирует демонстрационный PDF отчёт с тестовыми данными
    
    - **client_name**: Название клиента для заголовка отчёта
    """
    
    temp_pdf_path = None
    
    try:
        # Создаём временный файл для PDF
        temp_pdf_fd, temp_pdf_path = tempfile.mkstemp(suffix='.pdf')
        os.close(temp_pdf_fd)
        
        # Генерируем демо отчёт
        logger.info(f"Генерация демо отчёта для клиента: {client_name}")
        result_path = report_builder.generate_sample_report(
            client_name=client_name,
            output_path=temp_pdf_path
        )
        
        # Формируем имя файла
        safe_client_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"Демо_отчёт_{safe_client_name}.pdf"
        
        # Возвращаем PDF файл
        return FileResponse(
            path=result_path,
            filename=filename,
            media_type="application/pdf",
            background=_cleanup_temp_files(None, temp_pdf_path)
        )
        
    except Exception as e:
        # Очищаем временные файлы в случае ошибки
        if temp_pdf_path and os.path.exists(temp_pdf_path):
            os.unlink(temp_pdf_path)
        
        logger.error(f"Ошибка при генерации демо отчёта: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка генерации демо отчёта: {str(e)}"
        )


async def _cleanup_temp_files(excel_path: Optional[str], pdf_path: Optional[str]):
    """
    Асинхронная очистка временных файлов (для background tasks)
    """
    try:
        if excel_path and os.path.exists(excel_path):
            os.unlink(excel_path)
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
    except Exception as e:
        logger.warning(f"Не удалось очистить временные файлы: {e}")


def _cleanup_temp_files_sync(excel_path: Optional[str], pdf_path: Optional[str]):
    """
    Синхронная очистка временных файлов
    """
    try:
        if excel_path and os.path.exists(excel_path):
            os.unlink(excel_path)
        if pdf_path and os.path.exists(pdf_path):
            os.unlink(pdf_path)
    except Exception as e:
        logger.warning(f"Не удалось очистить временные файлы: {e}")


@router.get("/health")
async def reports_health():
    """Проверка работоспособности модуля генерации отчётов"""
    try:
        # Проверяем доступность шаблона
        builder = ReportBuilder()
        return {
            "status": "healthy",
            "service": "pdf_reports",
            "template_loaded": True
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "service": "pdf_reports",
            "error": str(e),
            "template_loaded": False
        }