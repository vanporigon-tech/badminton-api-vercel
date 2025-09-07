#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_room_sync():
    """Тестирование синхронизации комнат"""
    
    API_URL = "http://localhost:8000"
    
    print("🧪 ТЕСТИРОВАНИЕ СИНХРОНИЗАЦИИ КОМНАТ")
    print("=" * 50)
    
    try:
        # 1. Получаем все комнаты
        print("\n1️⃣ Получаем все комнаты...")
        response = requests.get(f"{API_URL}/rooms/")
        
        if response.status_code == 200:
            rooms = response.json()
            print(f"✅ Найдено комнат: {len(rooms)}")
            
            for room in rooms:
                print(f"  🏠 {room['name']} (ID: {room['id']})")
                print(f"     👥 Участников: {room['member_count']}/{room['max_players']}")
                print(f"     👑 Создатель: {room['creator_full_name']}")
                
                # Показываем участников
                if room['members']:
                    print(f"     👤 Участники:")
                    for member in room['members']:
                        player = member['player']
                        leader = "👑" if member['is_leader'] else "  "
                        print(f"       {leader} {player['first_name']} {player['last_name']}")
                print()
        else:
            print(f"❌ Ошибка получения комнат: {response.status_code}")
            return
        
        # 2. Создаем комнату от имени друга
        print("\n2️⃣ Создаем комнату от имени друга...")
        friend_data = {
            "name": "Комната Друга",
            "creator_telegram_id": 555666777,
            "max_players": 4
        }
        
        response = requests.post(f"{API_URL}/rooms/", json=friend_data)
        if response.status_code == 200:
            room = response.json()
            print(f"✅ Комната друга создана: {room['name']} (ID: {room['id']})")
        else:
            print(f"❌ Ошибка создания комнаты друга: {response.status_code}")
            print(f"Ответ: {response.text}")
        
        # 3. Проверяем, что комната появилась в списке
        print("\n3️⃣ Проверяем обновленный список комнат...")
        response = requests.get(f"{API_URL}/rooms/")
        
        if response.status_code == 200:
            rooms = response.json()
            print(f"✅ Обновленный список: {len(rooms)} комнат")
            
            # Ищем комнату друга
            friend_room = None
            for room in rooms:
                if room['creator_id'] == 555666777:
                    friend_room = room
                    break
            
            if friend_room:
                print(f"✅ Комната друга найдена: {friend_room['name']}")
            else:
                print("❌ Комната друга не найдена!")
        else:
            print(f"❌ Ошибка получения обновленного списка: {response.status_code}")
        
        print("\n🎉 ТЕСТ СИНХРОНИЗАЦИИ ЗАВЕРШЕН!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    test_room_sync()
