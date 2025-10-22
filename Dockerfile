FROM mcr.microsoft.com/playwright/python:v1.55.0-noble

# Установка системных зависимостей для GUI
RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    x11-apps \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2t64 \
    fonts-liberation \
    x11vnc \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

WORKDIR /app

# Создание скрипта для запуска с Xvfb
RUN echo '#!/bin/bash\n\
Xvfb :99 -screen 0 1920x1080x24 &\n\
export DISPLAY=:99\n\
exec "$@"' > /usr/local/bin/with-xvfb && \
    chmod +x /usr/local/bin/with-xvfb

# Установка браузеров Playwright
RUN playwright install

CMD ["with-xvfb", "python", "-m", "main.py"]