#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_api_fresh():
    """Тестирование API с новыми данными"""
    
    API_URL = "http://localhost:8000"
    
    print("🧪 Тестирование API с новыми данными...")
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
        
        # Тест 2: Создание нового игрока
        print("\n2️⃣ Создание нового игрока...")
        player_data = {
            "telegram_id": 999888777,
            "first_name": "Новый",
            "last_name": "Игрок",
            "username": "new_player"
        }
        
        response = requests.post(f"{API_URL}/players/", json=player_data)
        if response.status_code == 200:
            player = response.json()
            print(f"✅ Игрок создан: {player['first_name']} {player['last_name']}")
        else:
            print(f"❌ Ошибка создания игрока: {response.status_code}")
        
        # Тест 3: Создание новой комнаты
        print("\n3️⃣ Создание новой комнаты...")
        room_data = {
            "name": "Новая тестовая комната",
            "creator_telegram_id": 999888777,
            "max_players": 4
        }
        
        response = requests.post(f"{API_URL}/rooms/", json=room_data)
        if response.status_code == 200:
            room = response.json()
            print(f"✅ Комната создана: {room['name']} (ID: {room['id']})")
            room_id = room['id']
        else:
            print(f"❌ Ошибка создания комнаты: {response.status_code}")
            print(f"Ответ: {response.text}")
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
            "telegram_id": 111222333,
            "first_name": "Второй",
            "last_name": "Игрок",
            "username": "second_player"
        }
        
        response = requests.post(f"{API_URL}/rooms/{room_id}/join", json=join_data)
        if response.status_code == 200:
            join_result = response.json()
            print(f"✅ Присоединились к комнате: {join_result['room']['name']}")
            print(f"  Участников теперь: {join_result['room']['member_count']}")
        else:
            print(f"❌ Ошибка присоединения: {response.status_code}")
            print(f"Ответ: {response.text}")
        
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
        
        print("\n🎉 Все тесты пройдены! API работает корректно.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_api_fresh()
