#!/usr/bin/env python3
"""
Демонстрация работы всей системы Badminton Rating Mini App
"""

import os
import sys
import subprocess
import time
import requests

def print_header():
    """Вывод заголовка"""
    print("🏸" * 20)
    print("🏸 BADMINTON RATING MINI APP 🏸")
    print("🏸" * 20)
    print()

def check_dependencies():
    """Проверка зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    try:
        import fastapi
        print("✅ FastAPI установлен")
    except ImportError:
        print("❌ FastAPI не установлен")
        return False
    
    try:
        import psycopg2
        print("✅ psycopg2 установлен")
    except ImportError:
        print("❌ psycopg2 не установлен")
        return False
    
    try:
        import telegram
        print("✅ python-telegram-bot установлен")
    except ImportError:
        print("❌ python-telegram-bot не установлен")
        return False
    
    print("✅ Все зависимости установлены\n")
    return True

def check_environment():
    """Проверка переменных окружения"""
    print("🌍 Проверка переменных окружения...")
    
    required_vars = [
        'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD',
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_BOT_USERNAME'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}")
        return False
    
    print("✅ Все переменные окружения настроены\n")
    return True

def check_postgresql():
    """Проверка подключения к PostgreSQL"""
    print("🐘 Проверка подключения к PostgreSQL...")
    
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD')
        )
        conn.close()
        print("✅ Подключение к PostgreSQL успешно\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        print("💡 Убедитесь, что PostgreSQL запущен и база данных создана")
        return False

def test_telegram_bot():
    """Тест Telegram бота"""
    print("🤖 Тест Telegram бота...")
    
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот работает: @{bot_info.get('username')}")
                print(f"   Имя: {bot_info.get('first_name')}")
                return True
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def start_services():
    """Запуск сервисов"""
    print("🚀 Запуск сервисов...")
    
    print("1️⃣ Запуск FastAPI сервера...")
    print("   Команда: python3 run.py")
    print("   URL: http://localhost:8000")
    print("   Mini App: http://localhost:8000/app")
    print()
    
    print("2️⃣ Запуск Telegram бота...")
    print("   Команда: python3 bot.py")
    print("   Бот: @GoBadmikAppBot")
    print()
    
    print("3️⃣ Тестирование системы...")
    print("   Тест API: python3 test_app.py")
    print("   Тест бота: python3 test_bot.py")
    print("   Демо Glicko-2: python3 demo_glicko2.py")
    print()

def show_usage_instructions():
    """Показать инструкции по использованию"""
    print("📱 ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ")
    print("=" * 50)
    
    print("1️⃣ Настройка базы данных:")
    print("   python3 setup_database.py")
    print()
    
    print("2️⃣ Запуск в разных терминалах:")
    print("   Терминал 1: python3 run.py")
    print("   Терминал 2: python3 bot.py")
    print()
    
    print("3️⃣ Тестирование в браузере:")
    print("   Откройте: http://localhost:8000/app")
    print()
    
    print("4️⃣ Тестирование в Telegram:")
    print("   Найдите бота: @GoBadmikAppBot")
    print("   Отправьте: /start")
    print("   Нажмите кнопку '🏸 Открыть Badminton Rating'")
    print()
    
    print("5️⃣ Создание тестовой игры:")
    print("   - Создайте комнату")
    print("   - Добавьте игроков")
    print("   - Запустите игру")
    print("   - Введите счет")
    print("   - Посмотрите обновленные рейтинги")
    print()

def main():
    """Главная функция"""
    print_header()
    
    # Проверки
    if not check_dependencies():
        print("❌ Установите зависимости: pip3 install -r requirements.txt")
        return
    
    if not check_environment():
        print("❌ Настройте файл .env")
        return
    
    if not check_postgresql():
        print("❌ Настройте PostgreSQL")
        return
    
    if not test_telegram_bot():
        print("❌ Проверьте токен бота")
        return
    
    print("🎉 Все проверки пройдены успешно!")
    print("=" * 50)
    
    # Инструкции
    start_services()
    show_usage_instructions()
    
    print("🏆 Система готова к работе!")
    print("Удачной игры в бадминтон! 🏸")

if __name__ == "__main__":
    main()

