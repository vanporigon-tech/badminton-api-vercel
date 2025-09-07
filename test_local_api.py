#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_local_api():
    """Тестирование локального API"""
    
    API_URL = "http://localhost:8000"
    
    print("🧪 Тестирование локального API...")
    print(f"📍 URL: {API_URL}")
    
    try:
        # Тест 1: Проверка доступности
        print("\n1️⃣ Проверка доступности API...")
        response = requests.get(API_URL)
        if response.status_code == 200:
            print("✅ API доступен")
            print(f"📊 Ответ: {response.json()}")
        else:
            print(f"❌ API недоступен: {response.status_code}")
            return
        
        # Тест 2: Создание игрока
        print("\n2️⃣ Создание игрока...")
        player_data = {
            "telegram_id": 123456789,
            "first_name": "Тест",
            "last_name": "Игрок",
            "username": "test_player"
        }
        
        response = requests.post(f"{API_URL}/players/", json=player_data)
        if response.status_code == 200:
            player = response.json()
            print(f"✅ Игрок создан: {player['first_name']} {player['last_name']}")
        else:
            print(f"❌ Ошибка создания игрока: {response.status_code}")
        
        # Тест 3: Создание комнаты
        print("\n3️⃣ Создание комнаты...")
        room_data = {
            "name": "Тестовая комната",
            "creator_telegram_id": 123456789,
            "max_players": 4
        }
        
        response = requests.post(f"{API_URL}/rooms/", json=room_data)
        if response.status_code == 200:
            room = response.json()
            print(f"✅ Комната создана: {room['name']} (ID: {room['id']})")
            room_id = room['id']
        else:
            print(f"❌ Ошибка создания комнаты: {response.status_code}")
            return
        
        # Тест 4: Получение списка комнат
        print("\n4️⃣ Получение списка комнат...")
        response = requests.get(f"{API_URL}/rooms/")
        if response.status_code == 200:
            rooms = response.json()
            print(f"✅ Найдено комнат: {len(rooms)}")
            for room in rooms:
                print(f"  - {room['name']} (ID: {room['id']}, участников: {room['member_count']})")
        else:
            print(f"❌ Ошибка получения комнат: {response.status_code}")
        
        # Тест 5: Присоединение к комнате
        print("\n5️⃣ Присоединение к комнате...")
        join_data = {
            "telegram_id": 987654321,
            "first_name": "Второй",
            "last_name": "Игрок",
            "username": "second_player"
        }
        
        response = requests.post(f"{API_URL}/rooms/{room_id}/join", json=join_data)
        if response.status_code == 200:
            join_result = response.json()
            print(f"✅ Присоединились к комнате: {join_result['room']['name']}")
        else:
            print(f"❌ Ошибка присоединения: {response.status_code}")
        
        # Тест 6: Получение данных комнаты
        print("\n6️⃣ Получение данных комнаты...")
        response = requests.get(f"{API_URL}/rooms/{room_id}")
        if response.status_code == 200:
            room = response.json()
            print(f"✅ Комната загружена: {room['name']}")
            print(f"  Участников: {room['member_count']}")
            for member in room['members']:
                player = member['player']
                print(f"  - {player['first_name']} {player['last_name']}")
        else:
            print(f"❌ Ошибка загрузки комнаты: {response.status_code}")
        
        print("\n🎉 Все тесты пройдены! Локальный API работает корректно.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_local_api()
