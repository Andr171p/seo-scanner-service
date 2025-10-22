FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

# Устанавливаем xvfb
RUN apt-get update && apt-get install -y \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Используем xvfb-run для запуска приложения
CMD ["xvfb-run", "-a", "python", "main.py"]