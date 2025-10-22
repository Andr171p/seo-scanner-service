FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

# Установка Xvfb и графических зависимостей (исправленные пакеты)
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    x11-utils \
    xauth \
    libnss3 \
    libxss1 \
    libasound2t64 \
    libgtk-3-0 \
    libgbm-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

# Запуск через Xvfb
CMD ["xvfb-run", "-a", "python", "main.py"]