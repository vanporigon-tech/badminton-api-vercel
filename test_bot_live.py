#!/usr/bin/env python3
"""
Тестирование работающего Telegram бота
"""

import requests
import json

def test_bot_status():
    """Проверка статуса бота"""
    token = "8401405889:AAEGFi1tCX6k2m4MyGBoAY3MdJC63SXFba0"
    
    print("🧪 Тестирование работающего Telegram бота...")
    print("=" * 50)
    
    # Тест 1: Проверка информации о боте
    print("1️⃣ Проверка информации о боте...")
    url = f"https://api.telegram.org/bot{token}/getMe"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"✅ Бот работает: @{bot_info.get('username')}")
                print(f"   Имя: {bot_info.get('first_name')}")
                print(f"   ID: {bot_info.get('id')}")
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
                return False
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return False
    
    # Тест 2: Проверка webhook
    print("\n2️⃣ Проверка webhook...")
    url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data['result']
                print(f"✅ Webhook: {webhook_info.get('url', 'Не установлен')}")
                print(f"   Ожидает обновления: {webhook_info.get('pending_update_count', 0)}")
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    # Тест 3: Проверка команд
    print("\n3️⃣ Проверка команд бота...")
    url = f"https://api.telegram.org/bot{token}/getMyCommands"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                commands = data['result']
                print(f"✅ Команды настроены: {len(commands)}")
                for cmd in commands:
                    print(f"   /{cmd['command']} - {cmd['description']}")
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    # Тест 4: Проверка обновлений
    print("\n4️⃣ Проверка обновлений...")
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                updates = data['result']
                print(f"✅ Обновления получены: {len(updates)}")
                if updates:
                    print("   Последние обновления:")
                    for update in updates[-3:]:  # Показываем последние 3
                        if 'message' in update:
                            msg = update['message']
                            user = msg.get('from', {})
                            text = msg.get('text', 'Нет текста')
                            print(f"     От {user.get('first_name', 'Unknown')}: {text}")
                else:
                    print("   Нет новых обновлений")
            else:
                print(f"❌ Ошибка API: {data.get('description')}")
        else:
            print(f"❌ HTTP ошибка: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Тестирование завершено!")
    print("\n📱 Теперь вы можете:")
    print("1. Открыть Telegram")
    print("2. Найти бота: @GoBadmikAppBot")
    print("3. Отправить команду: /start")
    print("4. Нажать кнопку '🏸 Открыть Badminton Rating'")
    print("\n🌐 Убедитесь, что API сервер запущен:")
    print("   python3 main_simple.py")
    
    return True

if __name__ == "__main__":
    test_bot_status()

