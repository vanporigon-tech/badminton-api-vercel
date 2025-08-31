from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os
from datetime import datetime

# Создание FastAPI приложения
app = FastAPI(title="🏸 Badminton Rating API", version="1.0.0")

# CORS настройки
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все домены для простоты
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Простое хранилище в памяти (для начала)
players_db = {}
rooms_db = {}
room_counter = 1

# Pydantic модели
class PlayerCreate(BaseModel):
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None

class PlayerResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    last_name: Optional[str]
    username: Optional[str]
    rating: int = 1500

class RoomCreate(BaseModel):
    name: str
    creator_telegram_id: int
    max_players: int = 4

class RoomMemberResponse(BaseModel):
    id: int
    player: PlayerResponse
    is_leader: bool
    joined_at: str

class RoomResponse(BaseModel):
    id: int
    name: str
    creator_id: int
    creator_full_name: str
    max_players: int
    member_count: int
    is_active: bool
    created_at: str
    members: List[RoomMemberResponse] = []

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "🏸 Badminton Rating API",
        "version": "1.0.0",
        "status": "active",
        "database": "memory",
        "players": len(players_db),
        "rooms": len(rooms_db)
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "memory": {
            "players": len(players_db),
            "rooms": len(rooms_db)
        }
    }

@app.post("/players/", response_model=PlayerResponse)
async def create_or_get_player(player: PlayerCreate):
    """Создает или получает игрока по telegram_id"""
    if player.telegram_id in players_db:
        # Обновляем существующего игрока
        existing = players_db[player.telegram_id]
        existing.update({
            "first_name": player.first_name,
            "last_name": player.last_name,
            "username": player.username
        })
        return PlayerResponse(**existing)
    
    # Создаем нового игрока
    new_player = {
        "id": player.telegram_id,
        "telegram_id": player.telegram_id,
        "first_name": player.first_name,
        "last_name": player.last_name,
        "username": player.username,
        "rating": 1500
    }
    
    players_db[player.telegram_id] = new_player
    return PlayerResponse(**new_player)

@app.get("/players/{telegram_id}", response_model=PlayerResponse)
async def get_player(telegram_id: int):
    """Получает игрока по telegram_id"""
    if telegram_id not in players_db:
        return PlayerResponse(
            id=telegram_id,
            telegram_id=telegram_id,
            first_name="Неизвестный",
            last_name="Игрок",
            username=None,
            rating=1500
        )
    
    return PlayerResponse(**players_db[telegram_id])

@app.post("/rooms/", response_model=RoomResponse)
async def create_room(room: RoomCreate):
    """Создает новую комнату"""
    global room_counter
    
    # Получаем или создаем игрока
    if room.creator_telegram_id not in players_db:
        players_db[room.creator_telegram_id] = {
            "id": room.creator_telegram_id,
            "telegram_id": room.creator_telegram_id,
            "first_name": "Игрок",
            "last_name": f"{room.creator_telegram_id}",
            "username": None,
            "rating": 1500
        }
    
    creator = players_db[room.creator_telegram_id]
    creator_full_name = f"{creator['first_name']} {creator.get('last_name', '')}".strip()
    
    # Создаем комнату
    new_room = {
        "id": room_counter,
        "name": room.name,
        "creator_id": room.creator_telegram_id,
        "creator_full_name": creator_full_name,
        "max_players": room.max_players,
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
    
    return RoomResponse(**new_room)

@app.get("/rooms/", response_model=List[RoomResponse])
async def get_rooms():
    """Получает список всех активных комнат"""
    active_rooms = [room for room in rooms_db.values() if room.get("is_active", True)]
    return [RoomResponse(**room) for room in active_rooms]

@app.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(room_id: int):
    """Получает детали комнаты по ID"""
    if room_id not in rooms_db:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Комната не найдена")
    
    return RoomResponse(**rooms_db[room_id])

@app.delete("/rooms/{room_id}")
async def delete_room(room_id: int):
    """Удаляет комнату"""
    if room_id not in rooms_db:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Комната не найдена")
    
    del rooms_db[room_id]
    return {"message": "Комната успешно удалена"}

# Для Vercel
def handler(request, response):
    return app(request, response)