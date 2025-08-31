from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import os

from database import get_db, create_tables
from crud import (
    get_player_by_telegram_id, create_player, get_active_rooms, create_room,
    get_room_with_members, add_player_to_room, remove_player_from_room,
    start_game, create_game, calculate_game_ratings, get_player_stats
)
from schemas import (
    PlayerCreate, PlayerResponse, RoomCreate, RoomResponse, RoomDetailResponse,
    GameCreate, GameResponse, SuccessResponse, ErrorResponse, RoomSearchResponse
)
from models import Player
import models

app = FastAPI(
    title="Badminton Rating Mini App",
    description="Telegram Mini App for badminton rating calculation using Glicko-2 system",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Telegram domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

# Serve static files (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# API Routes
@app.get("/")
async def root():
    return {"message": "Badminton Rating Mini App API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Player endpoints
@app.post("/players/", response_model=PlayerResponse)
async def create_new_player(player: PlayerCreate, db: Session = Depends(get_db)):
    """Create a new player"""
    # Check if player already exists
    existing_player = get_player_by_telegram_id(db, player.telegram_id)
    if existing_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Player with this Telegram ID already exists"
        )
    
    return create_player(db, player)

@app.get("/players/{telegram_id}", response_model=PlayerResponse)
async def get_player(telegram_id: int, db: Session = Depends(get_db)):
    """Get player by Telegram ID"""
    player = get_player_by_telegram_id(db, telegram_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    return player

# Room endpoints
@app.post("/rooms/", response_model=RoomResponse)
async def create_new_room(room: RoomCreate, db: Session = Depends(get_db)):
    """Create a new room"""
    return create_room(db, room)

@app.get("/rooms/", response_model=RoomSearchResponse)
async def search_rooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get active rooms for joining"""
    from sqlalchemy.orm import joinedload
    
    # Get rooms with members and their player information
    rooms = db.query(models.Room).options(
        joinedload(models.Room.members).joinedload(models.RoomMember.player),
        joinedload(models.Room.creator)
    ).filter(models.Room.is_active == True).offset(skip).limit(limit).all()
    
    # Add member count and creator info to each room
    room_responses = []
    for room in rooms:
        member_count = len(room.members)
        creator_name = f"{room.creator.first_name} {room.creator.last_name}"
        members_names = [f"{member.player.first_name} {member.player.last_name}" for member in room.members]
        
        room_data = {
            'id': room.id,
            'name': room.name,
            'creator_id': room.creator_id,
            'max_players': room.max_players,
            'is_active': room.is_active,
            'is_game_started': room.is_game_started,
            'created_at': room.created_at,
            'updated_at': room.updated_at,
            'member_count': member_count,
            'creator_name': creator_name,
            'members_names': members_names
        }
        room_responses.append(RoomResponse(**room_data))
    
    return RoomSearchResponse(rooms=room_responses, total=len(room_responses))

@app.get("/rooms/{room_id}", response_model=RoomDetailResponse)
async def get_room_details(room_id: int, db: Session = Depends(get_db)):
    """Get room details with members"""
    room = get_room_with_members(db, room_id)
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room not found"
        )
    
    # Use the from_room class method to create response with proper names
    return RoomDetailResponse.from_room(room)

@app.post("/rooms/{room_id}/join")
async def join_room(room_id: int, player_id: int, db: Session = Depends(get_db)):
    """Join a room"""
    try:
        member = add_player_to_room(db, room_id, player_id)
        return SuccessResponse(message="Successfully joined room")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@app.post("/rooms/{room_id}/leave")
async def leave_room(room_id: int, player_id: int, db: Session = Depends(get_db)):
    """Leave a room"""
    success = remove_player_from_room(db, room_id, player_id)
    if success:
        return SuccessResponse(message="Successfully left room")
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found in room"
        )

@app.post("/rooms/{room_id}/start")
async def start_room_game(room_id: int, db: Session = Depends(get_db)):
    """Start a game in a room"""
    success = start_game(db, room_id)
    if success:
        return SuccessResponse(message="Game started successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start game - insufficient players"
        )

# Game endpoints
@app.post("/games/", response_model=GameResponse)
async def create_new_game(game: GameCreate, db: Session = Depends(get_db)):
    """Create a new game and calculate ratings"""
    # Create the game
    db_game = create_game(db, game)
    
    # Calculate new ratings
    success = calculate_game_ratings(db, db_game.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate ratings"
        )
    
    return db_game

@app.get("/players/{player_id}/stats")
async def get_player_statistics(player_id: int, db: Session = Depends(get_db)):
    """Get player statistics"""
    stats = get_player_stats(db, player_id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player not found"
        )
    return stats

# Serve the main HTML page
@app.get("/app", response_class=HTMLResponse)
async def serve_mini_app():
    """Serve the main Mini App HTML page"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Badminton Rating</title>
        <script src="https://telegram.org/js/telegram-web-app.js"></script>
        <link rel="stylesheet" href="/static/styles.css">
    </head>
    <body>
        <div id="app">
            <div class="header">
                <h1>🏸 Badminton Rating</h1>
                <p>Система рейтинга по Glicko-2</p>
            </div>
            
            <div id="main-menu" class="main-menu">
                <button id="search-game" class="btn btn-primary">
                    🔍 Искать игру
                </button>
                <button id="create-game" class="btn btn-secondary">
                    ➕ Создать игру
                </button>
            </div>
            
            <div id="search-rooms" class="section hidden">
                <h2>Доступные комнаты</h2>
                <div id="rooms-list" class="rooms-list"></div>
                <button id="back-to-main" class="btn btn-back">← Назад</button>
            </div>
            
            <div id="create-room" class="section hidden">
                <h2>Создать новую игру</h2>
                <form id="room-form">
                    <input type="text" id="room-name" placeholder="Название комнаты" required>
                    <button type="submit" class="btn btn-primary">Создать</button>
                </form>
                <button id="back-to-main-2" class="btn btn-back">← Назад</button>
            </div>
            
            <div id="room-details" class="section hidden">
                <h2 id="room-title"></h2>
                <div id="room-members" class="members-list"></div>
                <div id="room-actions" class="room-actions"></div>
                <button id="back-to-rooms" class="btn btn-back">← Назад к комнатам</button>
            </div>
            
            <div id="game-score" class="section hidden">
                <h2>Введите счет игры</h2>
                <form id="score-form">
                    <div class="score-inputs">
                        <div class="team-score">
                            <label>Команда 1</label>
                            <input type="number" id="score-team1" min="0" max="30" required>
                        </div>
                        <div class="vs">VS</div>
                        <div class="team-score">
                            <label>Команда 2</label>
                            <input type="number" id="score-team2" min="0" max="30" required>
                        </div>
                    </div>
                    <button type="submit" class="btn btn-primary">Завершить игру</button>
                </form>
                <button id="back-to-room" class="btn btn-back">← Назад в комнату</button>
            </div>
        </div>
        
        <script src="/static/app.js"></script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

