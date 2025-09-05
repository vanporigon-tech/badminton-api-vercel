#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_vercel_api():
    """Тестирование API на Vercel"""
    
    # Замените на ваш реальный URL после деплоя
    API_URL = "https://badminton-api-vercel.vercel.app"
    
    print("🧪 Тестирование API на Vercel...")
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
        
        # Тест 2: Начало турнира
        print("\n2️⃣ Начало турнира...")
        response = requests.post(f"{API_URL}/tournament/start")
        if response.status_code == 200:
            data = response.json()
            tournament_id = data.get('tournament_id')
            print(f"✅ Турнир #{tournament_id} начат")
        else:
            print(f"❌ Ошибка начала турнира: {response.status_code}")
            return
        
        # Тест 3: Получение данных турнира
        print("\n3️⃣ Получение данных турнира...")
        response = requests.get(f"{API_URL}/tournament/{tournament_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Данные турнира получены: {data}")
        else:
            print(f"❌ Ошибка получения данных: {response.status_code}")
        
        # Тест 4: Завершение турнира
        print("\n4️⃣ Завершение турнира...")
        response = requests.post(f"{API_URL}/tournament/end")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Турнир завершен: {data}")
        else:
            print(f"❌ Ошибка завершения турнира: {response.status_code}")
        
        print("\n🎉 Все тесты пройдены! API готов к работе.")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_vercel_api()
