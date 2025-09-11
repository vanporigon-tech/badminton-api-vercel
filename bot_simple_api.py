#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://vanporigon-tech.github.io/badminton-rating-app')
API_BASE_URL = os.getenv('API_BASE_URL', 'https://badminton-api-vercel.onrender.com')
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
        response = requests.post(url, json=data, timeout=15)
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
        response = requests.post(url, json=data, timeout=15)
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

def handle_start_command(chat_id, first_name, last_name="", username=""):
    """Обработка команды /start"""
    print(f"🚀 Обрабатываю команду /start для {first_name}")

    # Регистрируем/обновляем игрока через API (идемпотентно)
    display_name = first_name
    try:
        payload = {
            "telegram_id": chat_id,
            "first_name": first_name or "Игрок",
            "last_name": last_name or "",
            "username": username or ""
        }
        resp = requests.post(f"{API_BASE_URL}/players/", json=payload, timeout=15)
        if resp.status_code == 200:
            p = resp.json()
            fn = p.get("first_name") or first_name
            ln = p.get("last_name") or ""
            display_name = f"{fn} {ln}".strip()
    except Exception as e:
        print(f"⚠️ Не удалось зарегистрировать игрока в API: {e}")
    
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
        resp = requests.post(f"{API_BASE_URL}/players/set_rank", json=payload, timeout=10)
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


def handle_admin_clear_rooms(chat_id, user_id):
    """Админская команда очистки комнат через API"""
    print(f"🗑️ Админская команда очистки комнат от chat_id={chat_id} user_id={user_id}")
    if user_id not in ADMIN_IDS:
        return send_message(chat_id, "❌ У вас нет прав для выполнения этой команды.")
    try:
        send_message(chat_id, "⏳ Очищаю комнаты...")
        # Используем админский эндпоинт массовой очистки
        print(f"🔧 Очистка через API: {API_BASE_URL}/rooms/clear_all")
        dr = requests.delete(f"{API_BASE_URL}/rooms/clear_all", timeout=30)
        print(f"🔧 Результат очистки: status={dr.status_code} body={dr.text[:200]}")
        if dr.status_code == 200:
            data = dr.json()
            return send_message(chat_id, f"✅ Очистка завершена: rooms={data.get('rooms_deleted',0)}, members={data.get('members_deleted',0)}")
        else:
            return send_message(chat_id, f"❌ Ошибка очистки: {dr.status_code}")
    except Exception as e:
        return send_message(chat_id, f"❌ Ошибка очистки комнат: {e}")

_current_tournaments = {}

def handle_start_tournament(chat_id, user_id):
    """Начать турнир"""
    if user_id not in ADMIN_IDS:
        return send_message(chat_id, "❌ У вас нет прав для выполнения этой команды")
    
    try:
        # Проверяем нет ли активного турнира
        check = requests.get(f"{API_BASE_URL}/tournaments/active", timeout=15)
        if check.status_code == 200:
            t = check.json()
            _current_tournaments[chat_id] = t.get('id')
            return send_message(chat_id, f"⚠️ Уже есть активный турнир #{t.get('id')}. Сначала завершите его командой /end_tournament")
        resp = requests.post(f"{API_BASE_URL}/tournaments/start", json={}, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            tournament_id = data.get('id')
            _current_tournaments[chat_id] = tournament_id
            response_text = f"🏆 Турнир #{tournament_id} начат!\n\nВсе игры будут записываться в турнир до команды /end_tournament"
        else:
            response_text = f"❌ Ошибка начала турнира: {resp.status_code}"
            
        return send_message(chat_id, response_text)
        
    except Exception as e:
        print(f"❌ Ошибка при начале турнира: {e}")
        return send_message(chat_id, f"❌ Ошибка при начале турнира: {str(e)}")

def handle_end_tournament(chat_id, user_id):
    """Завершить турнир и отправить таблицу"""
    if user_id not in ADMIN_IDS:
        return send_message(chat_id, "❌ У вас нет прав для выполнения этой команды")
    
    try:
        # В системе может быть только один активный турнир — завершаем последний активный
        resp = requests.post(f"{API_BASE_URL}/tournaments/end_latest", json={}, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            _current_tournaments.pop(chat_id, None)
            tid = data.get('tournament_id')
            return send_message(chat_id, f"🏁 Турнир #{tid} завершен! Таблица: {data.get('sheet_url','')}")
        else:
            return send_message(chat_id, f"❌ Ошибка завершения турнира: {resp.status_code}")
        
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
        # Логируем все входящие обновления
        print(f"📨 Получено обновление: {update}")
        
        # Обработка сообщений
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            user_info = message.get("from", {})
            first_name = user_info.get("first_name", "Неизвестный")
            last_name = user_info.get("last_name", "")
            
            if "text" in message:
                text = message["text"]
                
                print(f"📝 Сообщение от {chat_id}: '{text}'")
                print(f"🔍 Проверяем права админа: {chat_id} in {ADMIN_IDS} = {chat_id in ADMIN_IDS}")
                user_id = user_info.get("id")
                print(f"🔍 user_id={user_id} admin={user_id in ADMIN_IDS if user_id else None}")
                
                if text == "/start":
                    username = user_info.get("username", "")
                    return handle_start_command(chat_id, first_name, last_name, username)
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
                elif text.strip().lower().startswith("/clear_rooms") or text == "/admin_clear_rooms":
                    print(f"🔄 Обрабатываем /clear_rooms от chat_id={chat_id} user_id={user_id}")
                    return handle_admin_clear_rooms(chat_id, user_id)
                elif text == "/start_tournament":
                    return handle_start_tournament(chat_id, user_id)
                elif text.startswith("/end_tournament"):
                    parts = text.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        if user_id not in ADMIN_IDS:
                            return send_message(chat_id, "❌ У вас нет прав для выполнения этой команды")
                        tid = int(parts[1])
                        try:
                            resp = requests.post(f"{API_BASE_URL}/tournaments/{tid}/end", json={}, timeout=30)
                            if resp.status_code == 200:
                                data = resp.json()
                                return send_message(chat_id, f"🏁 Турнир #{tid} завершен! Таблица: {data.get('sheet_url','')}")
                            else:
                                return send_message(chat_id, f"❌ Ошибка завершения: {resp.status_code}")
                        except Exception as e:
                            return send_message(chat_id, f"❌ Ошибка: {e}")
                    else:
                        return handle_end_tournament(chat_id, user_id)
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
    print("🤖 Запуск Telegram бота...")
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN не задан. Добавьте переменную окружения BOT_TOKEN и перезапустите.")
        return
    # Проверка токена
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
        if r.status_code != 200:
            print(f"❌ Неверный BOT_TOKEN или недоступен Telegram API: {r.status_code} {r.text}")
            return
        me = r.json().get('result', {})
        print(f"✅ Подключен как @{me.get('username','unknown')}")
    except Exception as e:
        print(f"❌ Не удалось проверить токен: {e}")
        return

    print(f"🌐 Mini App URL: {MINI_APP_URL}")
    print(f"🔗 API_BASE_URL: {API_BASE_URL}")
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
                    
                    print(f"🔄 Обрабатываем update_id: {update_id}")
                    
                    # Обрабатываем обновление
                    if not process_update(update):
                        print(f"❌ Ошибка обработки обновления {update_id}")
                    else:
                        print(f"✅ Успешно обработали update_id: {update_id}")
            
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
