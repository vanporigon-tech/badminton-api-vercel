from http.server import BaseHTTPRequestHandler
import json
import urllib.parse
from datetime import datetime

# Простое хранилище
players_db = {}
rooms_db = {}
room_counter = 1

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET запросов"""
        path = self.path.split('?')[0]
        
        # CORS заголовки
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            if path == '/':
                response = {
                    "message": "🏸 Badminton Rating API",
                    "version": "1.0.0",
                    "status": "active",
                    "database": "memory",
                    "players": len(players_db),
                    "rooms": len(rooms_db)
                }
                
            elif path == '/health':
                response = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat()
                }
                
            elif path == '/rooms/':
                # Возвращаем все комнаты
                active_rooms = [room for room in rooms_db.values() if room.get("is_active", True)]
                response = active_rooms
                
            elif path.startswith('/rooms/') and path != '/rooms/':
                # Получение конкретной комнаты
                room_id = int(path.split('/')[-1])
                if room_id in rooms_db:
                    response = rooms_db[room_id]
                else:
                    self.send_response(404)
                    response = {"error": "Комната не найдена"}
                    
            elif path.startswith('/players/'):
                # Получение игрока
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
            else:
                self.send_response(404)
                response = {"error": "Endpoint not found"}
                
        except Exception as e:
            self.send_response(500)
            response = {"error": str(e)}
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def do_POST(self):
        """Обработка POST запросов"""
        global room_counter
        
        # CORS заголовки
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            path = self.path.split('?')[0]
            
            if path == '/players/':
                # Создание/обновление игрока
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
                
            elif path == '/rooms/':
                # Создание комнаты
                creator_id = data['creator_telegram_id']
                
                # ПРОВЕРЯЕМ НЕ СОЗДАЛ ЛИ УЖЕ КОМНАТУ
                existing_room = None
                for room_id, room in rooms_db.items():
                    if room['creator_id'] == creator_id:
                        existing_room = room_id
                        break
                
                if existing_room:
                    self.send_response(400)
                    response = {"error": f"Вы уже создали комнату #{existing_room}. Можно создать только одну комнату."}
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
                
            elif path.startswith('/rooms/') and path.endswith('/join'):
                # Присоединение к комнате
                room_id = int(path.split('/')[-2])
                telegram_id = data['telegram_id']
                first_name = data.get('first_name', 'Игрок')
                last_name = data.get('last_name', '')
                username = data.get('username')
                
                if room_id not in rooms_db:
                    self.send_response(404)
                    response = {"error": "Комната не найдена"}
                else:
                    room = rooms_db[room_id]
                    
                    # Проверяем не присоединился ли уже
                    already_joined = any(member['player']['telegram_id'] == telegram_id for member in room['members'])
                    
                    if already_joined:
                        response = {"message": "Вы уже в комнате", "room": room}
                    elif len(room['members']) >= room['max_players']:
                        self.send_response(400)
                        response = {"error": "Комната заполнена"}
                    else:
                        # Создаем/обновляем игрока
                        if telegram_id not in players_db:
                            players_db[telegram_id] = {
                                "id": telegram_id,
                                "telegram_id": telegram_id,
                                "first_name": first_name,
                                "last_name": last_name,
                                "username": username,
                                "rating": 1500
                            }
                        else:
                            # Обновляем данные игрока
                            players_db[telegram_id].update({
                                "first_name": first_name,
                                "last_name": last_name,
                                "username": username
                            })
                        
                        player = players_db[telegram_id]
                        
                        # Добавляем игрока в комнату
                        new_member = {
                            "id": len(room['members']) + 1,
                            "player": player,
                            "is_leader": False,
                            "joined_at": datetime.now().isoformat()
                        }
                        
                        room['members'].append(new_member)
                        room['member_count'] = len(room['members'])
                        
                        # Обновляем комнату в базе
                        rooms_db[room_id] = room
                        
                        response = {
                            "message": "Успешно присоединились к комнате",
                            "room": room,
                            "member": new_member
                        }
                        
            elif path.startswith('/rooms/') and path.endswith('/leave'):
                # Выход из комнаты
                room_id = int(path.split('/')[-2])
                telegram_id = data['telegram_id']
                
                if room_id not in rooms_db:
                    self.send_response(404)
                    response = {"error": "Комната не найдена"}
                else:
                    room = rooms_db[room_id]
                    
                    # Находим участника для удаления
                    member_to_remove = None
                    for i, member in enumerate(room['members']):
                        if member['player']['telegram_id'] == telegram_id:
                            member_to_remove = i
                            break
                    
                    if member_to_remove is not None:
                        # Удаляем участника
                        removed_member = room['members'].pop(member_to_remove)
                        room['member_count'] = len(room['members'])
                        
                        # ЕСЛИ СОЗДАТЕЛЬ ПОКИДАЕТ КОМНАТУ - РАСФОРМИРОВЫВАЕМ ПОЛНОСТЬЮ
                        if room['creator_id'] == telegram_id:
                            # Создаем список участников для уведомления
                            remaining_members = [member['player']['telegram_id'] for member in room['members']]
                            
                            # Удаляем комнату полностью
                            del rooms_db[room_id]
                            
                            response = {
                                "message": "Комната расформирована",
                                "room_disbanded": True,
                                "affected_members": remaining_members
                            }
                        elif len(room['members']) == 0:
                            # Если комната пуста - удаляем её
                            del rooms_db[room_id]
                            response = {"message": "Вы покинули комнату. Комната удалена."}
                        else:
                            # Обычный выход участника
                            rooms_db[room_id] = room
                            response = {
                                "message": "Вы покинули комнату",
                                "room": room,
                                "removed_member": removed_member
                            }
                    else:
                        self.send_response(400)
                        response = {"error": "Вы не состоите в этой комнате"}
                
            else:
                self.send_response(404)
                response = {"error": "Endpoint not found"}
                
        except Exception as e:
            self.send_response(500)
            response = {"error": str(e)}
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def do_DELETE(self):
        """Обработка DELETE запросов"""
        # CORS заголовки
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            path = self.path.split('?')[0]
            
            if path.startswith('/rooms/') and path != '/rooms/':
                room_id = int(path.split('/')[-1])
                if room_id in rooms_db:
                    del rooms_db[room_id]
                    response = {"message": "Комната успешно удалена"}
                else:
                    self.send_response(404)
                    response = {"error": "Комната не найдена"}
            else:
                self.send_response(404)
                response = {"error": "Endpoint not found"}
                
        except Exception as e:
            self.send_response(500)
            response = {"error": str(e)}
        
        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """Обработка OPTIONS запросов для CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()