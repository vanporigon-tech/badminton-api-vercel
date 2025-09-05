#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import urllib.parse
import math
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# Простое хранилище
players_db = {}
rooms_db = {}
room_counter = 1

# Данные турниров
tournaments_db = {}
tournament_games = {}
tournament_counter = 0
current_tournament = None

# Система рейтинга Glicko-2 для бадминтона
class Glicko2Rating:
    def __init__(self, rating=1500, rd=350, vol=0.06):
        self.rating = rating
        self.rd = rd
        self.vol = vol

    def calculate_g(self, rd):
        return 1 / math.sqrt(1 + 3 * (rd ** 2) / (math.pi ** 2))

    def calculate_e(self, rating, other_rating, other_rd):
        g = self.calculate_g(other_rd)
        return 1 / (1 + math.exp(-g * (rating - other_rating) / 400))

    def update_rating(self, other_rating, other_rd, score):
        g = self.calculate_g(other_rd)
        e = self.calculate_e(self.rating, other_rating, other_rd)
        
        v = 1 / (g ** 2 * e * (1 - e))
        delta = v * g * (score - e)
        
        new_rating = self.rating + (self.rd ** 2 + v) * g * (score - e)
        new_rd = math.sqrt(1 / (1 / (self.rd ** 2) + 1 / v))
        
        return new_rating, new_rd

def calculate_team_rating(team_players, players_db):
    """Вычисляет средний рейтинг команды"""
    if not team_players:
        return 1500
    
    total_rating = sum(players_db[pid]['rating'] for pid in team_players if pid in players_db)
    return total_rating / len(team_players)

def calculate_rating_changes(room, score_data):
    """Вычисляет изменения рейтинга для всех игроков"""
    team1_players = [players_db[pid] for pid in score_data['team1'] if pid in players_db]
    team2_players = [players_db[pid] for pid in score_data['team2'] if pid in players_db]
    
    score1 = score_data['score1']
    score2 = score_data['score2']
    
    # Определяем победителей
    if score1 > score2:
        team1_won = True
        team2_won = False
    elif score2 > score1:
        team1_won = False
        team2_won = True
    else:
        team1_won = False
        team2_won = False
    
    changes = {}
    
    # Обновляем рейтинги для команды 1
    for player in team1_players:
        old_rating = player['rating']
        glicko = Glicko2Rating(old_rating, 350, 0.06)
        
        # Вычисляем средний рейтинг команды 2
        team2_rating = calculate_team_rating(score_data['team2'], players_db)
        team2_rd = 350  # Стандартное отклонение
        
        score = 1 if team1_won else 0 if team2_won else 0.5
        new_rating, new_rd = glicko.update_rating(team2_rating, team2_rd, score)
        
        rating_change = new_rating - old_rating
        
        # Обновляем рейтинг игрока
        player['rating'] = new_rating
        player['rd'] = new_rd
        
        changes[player['telegram_id']] = {
            'player_id': player['telegram_id'],
            'old_rating': old_rating,
            'new_rating': new_rating,
            'rating_change': rating_change,
            'team': 'team1'
        }
    
    # Обновляем рейтинги для команды 2
    for player in team2_players:
        old_rating = player['rating']
        glicko = Glicko2Rating(old_rating, 350, 0.06)
        
        # Вычисляем средний рейтинг команды 1
        team1_rating = calculate_team_rating(score_data['team1'], players_db)
        team1_rd = 350  # Стандартное отклонение
        
        score = 1 if team2_won else 0 if team1_won else 0.5
        new_rating, new_rd = glicko.update_rating(team1_rating, team1_rd, score)
        
        rating_change = new_rating - old_rating
        
        # Обновляем рейтинг игрока
        player['rating'] = new_rating
        player['rd'] = new_rd
        
        changes[player['telegram_id']] = {
            'player_id': player['telegram_id'],
            'old_rating': old_rating,
            'new_rating': new_rating,
            'rating_change': rating_change,
            'team': 'team2'
        }
    
    return list(changes.values())

def handler(request):
    """Обработчик для Vercel"""
    global room_counter, tournament_counter, current_tournament
    
    # CORS заголовки
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    if request.method == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}
    
    try:
        # Получаем данные запроса
        if request.method == 'POST':
            try:
                data = json.loads(request.body) if request.body else {}
            except:
                data = {}
        else:
            data = {}
        
        path = request.path
        print(f"🔍 {request.method} запрос: {path}, data: {data}")
        
        if path == '/':
            response = {
                "message": "Badminton Rating API",
                "status": "active",
                "database": "memory",
                "players": len(players_db),
                "rooms": len(rooms_db)
            }
            
        elif request.method == 'GET' and path == '/rooms/':
            response = list(rooms_db.values())
            
        elif request.method == 'GET' and path.startswith('/rooms/') and path != '/rooms/':
            room_id = int(path.split('/')[-1])
            if room_id in rooms_db:
                response = rooms_db[room_id]
            else:
                return {'statusCode': 404, 'headers': headers, 'body': json.dumps({"error": "Комната не найдена"})}
                
        elif request.method == 'GET' and path.startswith('/players/'):
            telegram_id = int(path.split('/')[-1])
            if telegram_id in players_db:
                response = players_db[telegram_id]
            else:
                response = {
                    "id": telegram_id,
                    "telegram_id": telegram_id,
                    "first_name": "Неизвестный",
                    "last_name": "Игрок",
                    "username": None,
                    "rating": 1500
                }
                
        elif request.method == 'GET' and path.startswith('/tournament/'):
            # Получение данных турнира
            tournament_id = int(path.split('/')[-1])
            if tournament_id not in tournaments_db:
                return {'statusCode': 404, 'headers': headers, 'body': json.dumps({"error": "Турнир не найден"})}
            else:
                tournament = tournaments_db[tournament_id]
                games = tournament_games.get(tournament_id, [])
                
                response = {
                    "tournament_id": tournament_id,
                    "tournament": tournament,
                    "games": games,
                    "message": f"Данные турнира #{tournament_id}"
                }
                
        elif request.method == 'POST' and path == '/players/':
            # Создание/обновление игрока
            if 'telegram_id' not in data:
                return {'statusCode': 400, 'headers': headers, 'body': json.dumps({"error": "telegram_id required"})}
            else:
                telegram_id = data['telegram_id']
                player = {
                    "id": telegram_id,
                    "telegram_id": telegram_id,
                    "first_name": data['first_name'],
                    "last_name": data.get('last_name'),
                    "username": data.get('username'),
                    "rating": 1500
                }
                players_db[telegram_id] = player
                response = player
                
        elif request.method == 'POST' and path == '/rooms/':
            # Создание комнаты
            if 'creator_telegram_id' not in data:
                return {'statusCode': 400, 'headers': headers, 'body': json.dumps({"error": "creator_telegram_id required"})}
            else:
                creator_id = data['creator_telegram_id']
                
                # ПРОВЕРЯЕМ НЕ СОЗДАЛ ЛИ УЖЕ КОМНАТУ
                existing_room = None
                for room_id, room in rooms_db.items():
                    if room['creator_id'] == creator_id:
                        existing_room = room_id
                        break
                
                if existing_room:
                    return {'statusCode': 400, 'headers': headers, 'body': json.dumps({"error": f"Вы уже создали комнату #{existing_room}. Можно создать только одну комнату."})}
                else:
                    # Создаем игрока если его нет
                    if creator_id not in players_db:
                        players_db[creator_id] = {
                            "id": creator_id,
                            "telegram_id": creator_id,
                            "first_name": "Игрок",
                            "last_name": f"{creator_id}",
                            "username": None,
                            "rating": 1500
                        }
                
                    creator = players_db[creator_id]
                    creator_full_name = f"{creator['first_name']} {creator.get('last_name', '')}".strip()
                    
                    # Создаем комнату
                    new_room = {
                        "id": room_counter,
                        "name": data['name'],
                        "creator_id": creator_id,
                        "creator_full_name": creator_full_name,
                        "max_players": data.get('max_players', 4),
                        "member_count": 1,
                        "is_active": True,
                        "created_at": datetime.now().isoformat(),
                        "members": [
                            {
                                "id": 1,
                                "player": creator,
                                "is_leader": True,
                                "joined_at": datetime.now().isoformat()
                            }
                        ]
                    }
                    
                    rooms_db[room_counter] = new_room
                    room_counter += 1
                    response = new_room
                    
        elif request.method == 'POST' and path == '/tournament/start':
            # Начать турнир
            tournament_counter += 1
            current_tournament = tournament_counter
            
            tournaments_db[current_tournament] = {
                "id": current_tournament,
                "start_time": datetime.now().isoformat(),
                "status": "active"
            }
            
            tournament_games[current_tournament] = []
            
            response = {
                "message": f"Турнир #{current_tournament} начат!",
                "tournament_id": current_tournament
            }
            
        elif request.method == 'POST' and path == '/tournament/end':
            # Завершить турнир
            if current_tournament is None:
                response = {"error": "Нет активного турнира"}
            else:
                tournament_id = current_tournament
                tournaments_db[tournament_id]["status"] = "finished"
                tournaments_db[tournament_id]["end_time"] = datetime.now().isoformat()
                
                current_tournament = None
                
                response = {
                    "message": f"Турнир #{tournament_id} завершен!",
                    "tournament_id": tournament_id
                }
                
        else:
            return {'statusCode': 404, 'headers': headers, 'body': json.dumps({"error": "Endpoint not found"})}
            
    except Exception as e:
        return {'statusCode': 500, 'headers': headers, 'body': json.dumps({"error": str(e)})}
    
    return {'statusCode': 200, 'headers': headers, 'body': json.dumps(response, ensure_ascii=False)}
