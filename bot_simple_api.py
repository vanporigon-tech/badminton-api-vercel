#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import os
import sqlite3
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '8401405889:AAEGFi1tCX6k2m4MyGBoAY3MdJC63SXFba0')
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://vanporigon-tech.github.io/badminton-rating-app')
def _load_admin_ids():
    env_value = os.getenv("ADMIN_IDS", "").strip()
    ids = {972717950, 1119274177}
    if env_value:
        for token in env_value.split(","):
            token = token.strip()
            if token.isdigit():
                ids.add(int(token))
    return ids

ADMIN_IDS = _load_admin_ids()



# Функции для работы с игроками удалены - по ТЗ данные хранятся в localStorage фронтенда

def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения в чат"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    
    if reply_markup:
        data["reply_markup"] = reply_markup
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print(f"✅ Сообщение отправлено успешно")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка отправки: {str(e)}")
        return False

def setup_bot_commands():
    """Настройка команд бота"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setMyCommands"
    
    commands = [
        {"command": "start", "description": "Запустить бота"},
        {"command": "help", "description": "Показать справку"},
        {"command": "clear_rooms", "description": "Очистить все комнаты (только админ)"},
        {"command": "start_tournament", "description": "Начать турнир (только админ)"},
        {"command": "end_tournament", "description": "Завершить турнир (только админ)"}
    ]
    
    data = {
        "commands": commands
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("✅ Команды бота настроены")
            print("📋 Доступные команды:")
            for cmd in commands:
                print(f"  /{cmd['command']} - {cmd['description']}")
            return True
        else:
            print(f"❌ Ошибка настройки команд: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ошибка настройки команд: {str(e)}")
        return False

def handle_start_command(chat_id, first_name, last_name=""):
    """Обработка команды /start"""
    print(f"🚀 Обрабатываю команду /start для {first_name}")
    
    # Создаем или обновляем игрока в базе данных
    player_info = get_or_create_player(chat_id, first_name, last_name)
    display_name = player_info['full_name'] if player_info else first_name
    
    # Создаем клавиатуру с кнопкой запуска игры
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "🏸 Начать игру",
                    "web_app": {
                        "url": MINI_APP_URL
                    }
                }
            ]
        ]
    }
    
    welcome_text = f"Привет, {display_name}! 👋\n\nВыберите ваш стартовый ранг (G → A). Вы можете написать в чат команду вида: /setrank G"
    
    return send_message(chat_id, welcome_text, keyboard)

def handle_help_command(chat_id):
    """Обработка команды /help"""
    print(f"❓ Обрабатываю команду /help для чата {chat_id}")
    
    help_text = """
🏸 <b>Справка по боту</b>

🎮 <b>Основные команды:</b>
/start - Запустить бота и открыть приложение
/help - Показать эту справку

👑 <b>Админские команды:</b>
/clear_rooms - Очистить все комнаты
/start_tournament - Начать турнир
/end_tournament - Завершить турнир

🌐 <b>Приложение:</b>
https://vanporigon-tech.github.io/badminton-rating-app

📊 <b>Система рейтинга:</b>
• Glicko-2 алгоритм
• Начальный рейтинг: 1500
• Поддержка 1v1 и 2v2 игр
• Автоматический расчет изменений

🏆 <b>Турниры:</b>
• Автоматическая запись всех игр
• Статистика участников
• Рейтинговая таблица
• Google Sheets интеграция

❓ <b>Помощь:</b>
Если у вас есть вопросы, обратитесь к администратору.
    """
    
    return send_message(chat_id, help_text)


def set_rank(chat_id, rank, first_name, last_name, username):
    rank = rank.upper()
    if rank not in ["G","F","E","D","C","B","A"]:
        return send_message(chat_id, "❌ Некорректный ранг. Доступны: G,F,E,D,C,B,A")
    try:
        # Call backend API to set rank
        payload = {
            "telegram_id": chat_id,
            "first_name": first_name or "Игрок",
            "last_name": last_name or "",
            "username": username,
            "initial_rank": rank
        }
        resp = requests.post("http://localhost:8000/players/set_rank", json=payload, timeout=10)
        if resp.status_code == 200:
            p = resp.json()
            return send_message(chat_id, f"✅ Ранг установлен: {rank}. Ваш рейтинг: {p.get('rating')}")
        else:
            return send_message(chat_id, f"⚠️ Не удалось установить ранг: {resp.status_code}")
    except Exception as e:
        return send_message(chat_id, f"❌ Ошибка установки ранга: {e}")

def handle_callback_query(chat_id, callback_data):
    """Обработка callback запросов от кнопок"""
    # Все callback запросы обрабатываются в мини-приложении
    return False


def handle_admin_clear_rooms(chat_id):
    """Админская команда очистки комнат (скрытая)"""
    print(f"🗑️ Админская команда очистки комнат от {chat_id}")
    
    if chat_id not in ADMIN_IDS:
        return send_message(chat_id, "❌ У вас нет прав для выполнения этой команды.")
    
    try:
        # Удаляем все комнаты из базы данных SQLite
        import sqlite3
        
        db_path = "badminton.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем количество комнат перед удалением
        cursor.execute("SELECT COUNT(*) FROM rooms")
        rooms_count = cursor.fetchone()[0]
        
        # Удаляем все комнаты
        cursor.execute("DELETE FROM rooms")
        
        # Сбрасываем автоинкремент
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='rooms'")
        
        conn.commit()
        conn.close()
        
        success_message = f"✅ Удалено комнат: {rooms_count}\n💣 Все комнаты успешно очищены и расформированы!\n🔄 Счетчик ID сброшен.\n\n⚠️ ВАЖНО: Все пользователи должны обновить страницу Mini App для применения изменений!"
        print(f"✅ Удалено {rooms_count} комнат из базы данных")
        
    except Exception as e:
        print(f"❌ Ошибка очистки комнат: {str(e)}")
        success_message = f"❌ Ошибка при очистке комнат: {str(e)}"
    
    return send_message(chat_id, success_message)

def handle_start_tournament(chat_id):
    """Начать турнир"""
    if chat_id not in ADMIN_IDS:
        return send_message(chat_id, "❌ У вас нет прав для выполнения этой команды")
    
    try:
        # Отправляем запрос в API для начала турнира
        response = requests.get("https://vanporigon-tech.github.io/badminton-rating-app/api/tournament/start.json")
        
        if response.status_code == 200:
            data = response.json()
            tournament_id = data.get('tournament_id')
            response_text = f"🏆 Турнир #{tournament_id} начат!\n\nВсе игры будут записываться в турнир до команды /end_tournament"
        else:
            response_text = f"❌ Ошибка начала турнира: {response.status_code}"
            
        return send_message(chat_id, response_text)
        
    except Exception as e:
        print(f"❌ Ошибка при начале турнира: {e}")
        return send_message(chat_id, f"❌ Ошибка при начале турнира: {str(e)}")

def handle_end_tournament(chat_id):
    """Завершить турнир и отправить таблицу"""
    if chat_id not in ADMIN_IDS:
        return send_message(chat_id, "❌ У вас нет прав для выполнения этой команды")
    
    try:
        # Завершаем турнир в API
        response = requests.get("https://vanporigon-tech.github.io/badminton-rating-app/api/tournament/end.json")
        
        if response.status_code == 200:
            data = response.json()
            tournament_id = data.get('tournament_id')
            
            # Получаем данные турнира
            data_response = requests.get(f"https://vanporigon-tech.github.io/badminton-rating-app/api/tournament/{tournament_id}.json")
            
            if data_response.status_code == 200:
                tournament_data = data_response.json()
                
                # Создаем Google Таблицу
                table_url = create_tournament_table(tournament_id, tournament_data)
                
                response_text = f"🏆 Турнир #{tournament_id} завершен!\n\n📊 Результаты: {table_url}"
            else:
                response_text = f"🏆 Турнир #{tournament_id} завершен!\n\n❌ Ошибка получения данных: {data_response.status_code}"
        else:
            response_text = f"❌ Ошибка завершения турнира: {response.status_code}"
            
        return send_message(chat_id, response_text)
        
    except Exception as e:
        print(f"❌ Ошибка при завершении турнира: {e}")
        return send_message(chat_id, f"❌ Ошибка при завершении турнира: {str(e)}")

def create_tournament_table(tournament_id, data):
    """Создать Google Таблицу с результатами турнира"""
    from google_sheets import create_tournament_table as create_sheets_table
    return create_sheets_table(tournament_id, data)

def process_update(update):
    """Обработка обновления от Telegram"""
    try:
        # Обработка сообщений
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_info = message.get("from", {})
            first_name = user_info.get("first_name", "Неизвестный")
            last_name = user_info.get("last_name", "")
            
            if "text" in message:
                text = message["text"]
                
                if text == "/start":
                    return handle_start_command(chat_id, first_name, last_name)
                elif text == "/help":
                    return handle_help_command(chat_id)
                elif text.lower().startswith("/setrank"):
                    parts = text.split()
                    if len(parts) >= 2:
                        rank = parts[1].strip()
                        username = user_info.get("username")
                        return set_rank(chat_id, rank, first_name, last_name, username)
                    else:
                        return send_message(chat_id, "Введите команду /setrank <ранг> (G..A)")
                elif text == "/admin_clear_rooms":
                    return handle_admin_clear_rooms(chat_id)
                elif text == "/start_tournament":
                    return handle_start_tournament(chat_id)
                elif text == "/end_tournament":
                    return handle_end_tournament(chat_id)
                else:
                    # Игнорируем все остальные команды
                    return True
        
        # Обработка callback запросов от кнопок
        elif "callback_query" in update:
            callback_query = update["callback_query"]
            chat_id = callback_query["message"]["chat"]["id"]
            callback_data = callback_query["data"]
            
            return handle_callback_query(chat_id, callback_data)
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обработки обновления: {str(e)}")
        return False

def get_updates(offset=None):
    """Получение обновлений от Telegram"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    
    params = {
        "timeout": 30,
        "allowed_updates": ["message", "callback_query"]
    }
    
    if offset:
        params["offset"] = offset
    
    try:
        response = requests.get(url, params=params, timeout=35)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Ошибка получения обновлений: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Ошибка получения обновлений: {str(e)}")
        return None

def main():
    """Основная функция бота"""
    print("🤖 Запуск простого Telegram бота...")
    print(f"📱 Токен: {BOT_TOKEN[:20]}...")
    print(f"🌐 Mini App URL: {MINI_APP_URL}")
    print("=" * 50)
    
    # Настраиваем команды бота
    if not setup_bot_commands():
        print("❌ Не удалось настроить команды бота")
        return
    
    print("✅ Бот успешно запущен!")
    print("📱 Отправьте /start в Telegram боту @GoBadmikAppBot")
    print("=" * 50)
    
    offset = None
    
    while True:
        try:
            print("🔄 Бот работает... Нажмите Ctrl+C для остановки")
            
            # Получаем обновления
            updates_response = get_updates(offset)
            
            if updates_response and "result" in updates_response:
                updates = updates_response["result"]
                
                for update in updates:
                    update_id = update["update_id"]
                    offset = update_id + 1
                    
                    # Обрабатываем обновление
                    if not process_update(update):
                        print(f"❌ Ошибка обработки обновления {update_id}")
            
            # Небольшая пауза между запросами
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n🛑 Бот остановлен пользователем")
            break
        except Exception as e:
            print(f"❌ Критическая ошибка: {str(e)}")
            time.sleep(5)  # Пауза перед повторной попыткой

if __name__ == "__main__":
    main()
