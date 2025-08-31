#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для тестирования и настройки системы
"""

import os
import sys
from sqlalchemy import create_engine
from database_sqlite import create_tables, SessionLocal
from crud_sqlite import create_player, get_player_by_telegram_id
from schemas import PlayerCreate

def test_database_setup():
    """Тестирование настройки базы данных"""
    print("🔧 Создание таблиц базы данных...")
    
    try:
        create_tables()
        print("✅ Таблицы созданы успешно!")
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False
    
    # Тестируем создание игрока
    db = SessionLocal()
    try:
        print("🧪 Тестирование создания игрока...")
        
        # Проверяем, существует ли тестовый пользователь
        test_telegram_id = 123456789
        existing_player = get_player_by_telegram_id(db, test_telegram_id)
        
        if not existing_player:
            test_player = PlayerCreate(
                telegram_id=test_telegram_id,
                first_name='Тест',
                last_name='Игрок'
            )
            new_player = create_player(db, test_player)
            print(f"✅ Создан тестовый игрок: {new_player.first_name} {new_player.last_name} (ID: {new_player.id})")
        else:
            print(f"✅ Тестовый игрок уже существует: {existing_player.first_name} {existing_player.last_name} (ID: {existing_player.id})")
        
        print("🎯 База данных готова к работе!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        return False
    finally:
        db.close()

def test_room_creation():
    """Тестирование создания комнаты с полным именем создателя"""
    from crud_sqlite import create_room, get_room_with_members
    from schemas import RoomCreate
    
    db = SessionLocal()
    try:
        print("🏠 Тестирование создания комнаты...")
        
        # Получаем тестового игрока
        test_player = get_player_by_telegram_id(db, 123456789)
        if not test_player:
            print("❌ Тестовый игрок не найден")
            return False
        
        # Создаем комнату
        test_room = RoomCreate(
            name="Тестовая игра",
            creator_id=test_player.id
        )
        
        new_room = create_room(db, test_room)
        print(f"✅ Создана комната: {new_room.name}")
        
        # Получаем детали комнаты
        room_with_members = get_room_with_members(db, new_room.id)
        if room_with_members:
            print(f"📝 Создатель: {room_with_members.creator.first_name} {room_with_members.creator.last_name}")
            print(f"👥 Участники: {len(room_with_members.members)}")
            for member in room_with_members.members:
                role = "Лидер" if member.is_leader else "Участник"
                print(f"   - {member.player.first_name} {member.player.last_name} ({role})")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания комнаты: {e}")
        return False
    finally:
        db.close()

def main():
    """Основная функция"""
    print("🚀 Запуск тестирования системы бадминтона...")
    print("=" * 50)
    
    # Тестируем базу данных
    if not test_database_setup():
        print("❌ Ошибка настройки базы данных")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    
    # Тестируем создание комнат
    if not test_room_creation():
        print("❌ Ошибка создания комнат")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 Все тесты прошли успешно!")
    print("🏸 Система готова к использованию!")

if __name__ == "__main__":
    main()
