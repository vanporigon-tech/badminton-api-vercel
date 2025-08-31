#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from database_sqlite import get_db, SessionLocal
from crud_sqlite import get_player_by_telegram_id, create_player
from schemas import PlayerCreate

# Загружаем переменные окружения
load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN', '8401405889:AAEGFi1tCX6k2m4MyGBoAY3MdJC63SXFba0')
MINI_APP_URL = os.getenv('MINI_APP_URL', 'https://vanporigon-tech.github.io/badminton-rating-app')
ADMIN_CHAT_ID = 972717950

# Состояния пользователей
user_states = {}

def get_db_session():
    """Получить сессию базы данных"""
    return SessionLocal()

def get_or_create_player(telegram_id: int, first_name: str, last_name: str = "") -> dict:
    """Получить или создать игрока в базе данных"""
    db = get_db_session()
    try:
        # Попытаться найти существующего игрока
        player = get_player_by_telegram_id(db, telegram_id)
        
        if player:
            # Обновить имя если оно изменилось
            if first_name and (player.first_name != first_name or player.last_name != last_name):
                player.first_name = first_name
                if last_name:  # Обновляем фамилию только если она передана
                    player.last_name = last_name
                db.commit()
                db.refresh(player)
            return {
                'id': player.id,
                'telegram_id': player.telegram_id,
                'first_name': player.first_name,
                'last_name': player.last_name,
                'full_name': f"{player.first_name} {player.last_name}"
            }
        else:
            # Создать нового игрока
            if not last_name:
                last_name = "Неуказано"  # Значение по умолчанию
            
            player_data = PlayerCreate(
                telegram_id=telegram_id,
                first_name=first_name,
                last_name=last_name
            )
            new_player = create_player(db, player_data)
            return {
                'id': new_player.id,
                'telegram_id': new_player.telegram_id,
                'first_name': new_player.first_name,
                'last_name': new_player.last_name,
                'full_name': f"{new_player.first_name} {new_player.last_name}"
            }
    except Exception as e:
        print(f"❌ Ошибка работы с базой данных: {str(e)}")
        return None
    finally:
        db.close()

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
        {"command": "start", "description": "Запустить бота"}
    ]
    
    data = {
        "commands": commands
    }
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            print("✅ Команды бота настроены")
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
    
    # Создаем клавиатуру с двумя кнопками
    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "✏️ Изменить инициалы",
                    "callback_data": "change_initials"
                }
            ],
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
    
    welcome_text = f"Привет, {display_name}! 👋"
    
    return send_message(chat_id, welcome_text, keyboard)

def handle_callback_query(chat_id, callback_data):
    """Обработка callback запросов от кнопок"""
    if callback_data == "change_initials":
        # Устанавливаем состояние пользователя
        user_states[chat_id] = "waiting_for_name"
        
        # Запрашиваем имя и фамилию
        response_text = "✏️ Отправьте ваше имя и фамилию в одном сообщении"
        
        return send_message(chat_id, response_text)
    
    return False

def handle_name_input(chat_id, text, first_name):
    """Обработка ввода имени и фамилии"""
    print(f"✏️ Обрабатываю ввод имени для {first_name}")
    
    # Парсим введенное имя и фамилию
    parts = text.strip().split()
    
    if len(parts) < 2:
        error_text = "❌ Введите имя и фамилию"
        return send_message(chat_id, error_text)
    
    # Извлекаем имя и фамилию
    new_first_name = parts[0]
    new_last_name = ' '.join(parts[1:])  # Фамилия может состоять из нескольких слов
    
    # Обновляем имя в базе данных
    player_info = get_or_create_player(chat_id, new_first_name, new_last_name)
    
    if player_info:
        success_text = f"✅ Имя обновлено: {player_info['full_name']}"
    else:
        success_text = f"✅ Имя сохранено: {new_first_name} {new_last_name}"
    
    # Сбрасываем состояние пользователя
    if chat_id in user_states:
        del user_states[chat_id]
    
    return send_message(chat_id, success_text)

def handle_admin_clear_rooms(chat_id):
    """Админская команда очистки комнат (скрытая)"""
    print(f"🗑️ Админская команда очистки комнат от {chat_id}")
    
    if chat_id != ADMIN_CHAT_ID:
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
        
        success_message = f"✅ Удалено комнат: {rooms_count}\n💣 Все комнаты успешно очищены и расформированы!\n🔄 Счетчик ID сброшен."
        print(f"✅ Удалено {rooms_count} комнат из базы данных")
        
    except Exception as e:
        print(f"❌ Ошибка очистки комнат: {str(e)}")
        success_message = f"❌ Ошибка при очистке комнат: {str(e)}"
    
    return send_message(chat_id, success_message)

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
                elif text == "/admin_clear_rooms":
                    return handle_admin_clear_rooms(chat_id)
                elif chat_id in user_states and user_states[chat_id] == "waiting_for_name":
                    # Пользователь вводит имя и фамилию
                    return handle_name_input(chat_id, text, first_name)
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
