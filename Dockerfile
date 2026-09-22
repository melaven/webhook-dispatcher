FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    libffi-dev \
    wget \
    dos2unix \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libjpeg-dev \
    libopenjp2-7-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя
RUN groupadd -g 1001 tenable && \
    useradd -u 1001 -g tenable -s /bin/bash -m tenable

# Установка рабочей директории
WORKDIR /app

# Копирование файлов зависимостей
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY --chown=tenable:tenable . .

# Создание директории data и установка прав
RUN mkdir -p /app/data && chown tenable:tenable /app/data

# Исправление окончаний строк для всех текстовых файлов
RUN find /app -type f -name "*.py" -exec dos2unix {} \; && \
    find /app -type f -name "*.txt" -exec dos2unix {} \; && \
    find /app -type f -name "*.yml" -exec dos2unix {} \; && \
    find /app -type f -name "*.yaml" -exec dos2unix {} \;

# Переключение на unprivileged пользователя
USER tenable

# Переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Порт приложения
EXPOSE 8000

# Команда запуска
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]