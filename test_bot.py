#!/usr/bin/env python3
"""
Тестирование Telegram бота
"""

import requests
import json

def test_bot_info():
    """Получение информации о боте"""
    token = "8401405889:AAEGFi1tCX6k2m4MyGBoAY3MdJC63SXFba0"
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print("✅ Информация о боте получена:")
                print(f"   Имя: {bot_info.get('first_name')}")
                print(f"   Username: @{bot_info.get('username')}")
                print(f"   ID: {bot_info.get('id')}")
                print(f"   Может присоединяться к группам: {bot_info.get('can_join_groups')}")
                print(f"   Может читать сообщения: {bot_info.get('can_read_all_group_messages')}")
                print(f"   Поддерживает inline режим: {bot_info.get('supports_inline_queries')}")
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

def test_webhook_info():
    """Получение информации о webhook"""
    token = "8401405889:AAEGFi1tCX6k2m4MyGBoAY3MdJC63SXFba0"
    url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data['result']
                print("\n📡 Информация о webhook:")
                print(f"   URL: {webhook_info.get('url', 'Не установлен')}")
                print(f"   Ожидает обновления: {webhook_info.get('pending_update_count', 0)}")
                print(f"   Последняя ошибка: {webhook_info.get('last_error_message', 'Нет')}")
                print(f"   Последняя ошибка времени: {webhook_info.get('last_error_date', 'Нет')}")
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

def test_set_commands():
    """Установка команд бота"""
    token = "8401405889:AAEGFi1tCX6k2m4MyGBoAY3MdJC63SXFba0"
    url = f"https://api.telegram.org/bot{token}/setMyCommands"
    
    commands = [
        {"command": "start", "description": "🏸 Запустить Badminton Rating"},
        {"command": "help", "description": "🔍 Справка по командам"},
        {"command": "rating", "description": "🏆 Информация о системе рейтинга"},
        {"command": "about", "description": "ℹ️ О проекте"}
    ]
    
    data = {"commands": commands}
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print("✅ Команды бота установлены успешно!")
                return True
            else:
                print(f"❌ Ошибка установки команд: {result.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 Тестирование Telegram бота...")
    print("=" * 50)
    
    # Тест информации о боте
    if not test_bot_info():
        print("❌ Не удалось получить информацию о боте")
        return
    
    # Тест webhook
    test_webhook_info()
    
    # Тест установки команд
    if test_set_commands():
        print("\n🎉 Бот настроен и готов к работе!")
        print("\n📱 Теперь вы можете:")
        print("1. Найти бота в Telegram")
        print("2. Отправить команду /start")
        print("3. Открыть Mini App")
        print("\n🚀 Для запуска бота выполните:")
        print("  python bot.py")
    else:
        print("\n❌ Не удалось настроить команды бота")

if __name__ == "__main__":
    main()

