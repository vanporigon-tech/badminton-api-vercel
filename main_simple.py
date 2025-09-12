#!/usr/bin/env python3
"""
Упрощенная версия Badminton Rating Mini App с SQLite для тестирования
"""

from fastapi import FastAPI, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import json
from datetime import datetime
import os

# Создаем SQLite базу данных
def init_db():
    """Инициализация SQLite базы данных"""
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    # Создаем таблицы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            rating REAL DEFAULT 1500.0,
            rd REAL DEFAULT 350.0,
            volatility REAL DEFAULT 0.06,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            creator_id INTEGER NOT NULL,
            max_players INTEGER DEFAULT 4,
            is_active BOOLEAN DEFAULT 1,
            is_game_started BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS room_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            player_id INTEGER NOT NULL,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_leader BOOLEAN DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            score_team1 INTEGER NOT NULL,
            score_team2 INTEGER NOT NULL,
            winner_team INTEGER NOT NULL,
            played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Инициализируем базу данных
init_db()

app = FastAPI(
    title="Badminton Rating Mini App (SQLite)",
    description="Telegram Mini App для бадминтона с SQLite",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic модели
class PlayerCreate(BaseModel):
    telegram_id: int
    first_name: str
    last_name: str
    rating: float = 1500.0

class RoomCreate(BaseModel):
    name: str
    creator_id: int

class GameCreate(BaseModel):
    room_id: int
    score_team1: int
    score_team2: int

# API endpoints
@app.get("/")
async def root():
    return {"message": "Badminton Rating Mini App (SQLite)", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "SQLite"}

@app.post("/players/")
async def create_player(player: PlayerCreate):
    """Создание игрока"""
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO players (telegram_id, first_name, last_name, rating)
            VALUES (?, ?, ?, ?)
        ''', (player.telegram_id, player.first_name, player.last_name, player.rating))
        
        conn.commit()
        player_id = cursor.lastrowid
        
        return {
            "id": player_id,
            "telegram_id": player.telegram_id,
            "first_name": player.first_name,
            "last_name": player.last_name,
            "rating": player.rating,
            "rd": 350.0,
            "volatility": 0.06
        }
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Игрок уже существует")
    finally:
        conn.close()

@app.get("/players/{telegram_id}")
async def get_player(telegram_id: int):
    """Получение игрока по Telegram ID"""
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM players WHERE telegram_id = ?', (telegram_id,))
    player = cursor.fetchone()
    conn.close()
    
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    
    return {
        "id": player[0],
        "telegram_id": player[1],
        "first_name": player[2],
        "last_name": player[3],
        "rating": player[4],
        "rd": player[5],
        "volatility": player[6],
        "created_at": player[7]
    }

@app.post("/rooms/")
async def create_room(room: RoomCreate):
    """Создание новой комнаты"""
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    try:
        # Проверяем, не создал ли уже пользователь комнату
        cursor.execute('SELECT id FROM rooms WHERE creator_id = ? AND is_active = 1', (room.creator_id,))
        existing_room = cursor.fetchone()
        
        if existing_room:
            raise HTTPException(
                status_code=400, 
                detail="Вы уже создали активную комнату. Сначала завершите или удалите существующую."
            )
        
        # Создаем комнату
        cursor.execute('''
            INSERT INTO rooms (name, creator_id, max_players, is_active, is_game_started)
            VALUES (?, ?, ?, ?, ?)
        ''', (room.name, room.creator_id, 4, True, False))
        
        room_id = cursor.lastrowid
        
        # Добавляем создателя как участника и лидера
        cursor.execute('''
            INSERT INTO room_members (room_id, player_id, is_leader)
            VALUES (?, ?, ?)
        ''', (room_id, room.creator_id, True))
        
        conn.commit()
        
        return {
            "id": room_id,
            "name": room.name,
            "creator_id": room.creator_id,
            "max_players": 4,
            "is_active": True,
            "is_game_started": False,
            "member_count": 1
        }
        
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Ошибка создания комнаты")
    finally:
        conn.close()

@app.get("/rooms/")
async def get_rooms():
    """Получение списка комнат"""
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.*, COUNT(rm.id) as member_count
        FROM rooms r
        LEFT JOIN room_members rm ON r.id = rm.room_id
        WHERE r.is_active = 1
        GROUP BY r.id
    ''')
    
    rooms = []
    for row in cursor.fetchall():
        rooms.append({
            "id": row[0],
            "name": row[1],
            "creator_id": row[2],
            "max_players": row[3],
            "is_active": bool(row[4]),
            "is_game_started": bool(row[5]),
            "member_count": row[7] or 0
        })
    
    conn.close()
    return {"rooms": rooms, "total": len(rooms)}

@app.get("/rooms/{room_id}")
async def get_room(room_id: int):
    """Получение деталей комнаты"""
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    # Получаем информацию о комнате
    cursor.execute('SELECT * FROM rooms WHERE id = ?', (room_id,))
    room = cursor.fetchone()
    
    if not room:
        conn.close()
        raise HTTPException(status_code=404, detail="Комната не найдена")
    
    # Получаем участников
    cursor.execute('''
        SELECT rm.*, p.first_name, p.last_name, p.rating
        FROM room_members rm
        JOIN players p ON rm.player_id = p.id
        WHERE rm.room_id = ?
    ''', (room_id,))
    
    members = []
    for row in cursor.fetchall():
        members.append({
            "id": row[0],
            "player": {
                "id": row[2],
                "first_name": row[4],
                "last_name": row[5],
                "rating": row[6]
            },
            "joined_at": row[3],
            "is_leader": bool(row[1])
        })
    
    conn.close()
    
    return {
        "id": room[0],
        "name": room[1],
        "creator_id": room[2],
        "max_players": room[3],
        "is_active": bool(room[4]),
        "is_game_started": bool(room[5]),
        "member_count": len(members),
        "members": members
    }

@app.get("/rooms/{room_id}/members")
async def get_room_members(room_id: int):
    """Получение списка участников комнаты"""
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    try:
        # Получаем участников с их именами
        cursor.execute('''
            SELECT rm.player_id, rm.is_leader, p.first_name, p.last_name, p.rating
            FROM room_members rm
            JOIN players p ON rm.player_id = p.telegram_id
            WHERE rm.room_id = ?
            ORDER BY rm.is_leader DESC, p.first_name
        ''', (room_id,))
        
        members = []
        for row in cursor.fetchall():
            player_id, is_leader, first_name, last_name, rating = row
            members.append({
                "player_id": player_id,
                "is_leader": bool(is_leader),
                "name": f"{first_name} {last_name}",
                "rating": rating
            })
        
        return {
            "room_id": room_id,
            "members": members,
            "total_count": len(members)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения участников: {str(e)}")
    finally:
        conn.close()

@app.post("/rooms/{room_id}/join")
async def join_room(room_id: int, player_id: int | None = Query(None), telegram_id: int | None = Query(None)):
    """Присоединение к комнате. Принимает player_id или telegram_id."""
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()

    try:
        # Разрешаем telegram_id → player_id, если явно не передали player_id
        if player_id is None:
            if telegram_id is None:
                raise HTTPException(status_code=400, detail="Не указан player_id или telegram_id")
            cursor.execute('SELECT id FROM players WHERE telegram_id = ?', (telegram_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Игрок не найден")
            player_id = int(row[0])

        # Проверяем, не в комнате ли уже игрок
        cursor.execute('SELECT id FROM room_members WHERE room_id = ? AND player_id = ?', (room_id, player_id))
        if cursor.fetchone():
            return {"success": True, "message": "Уже в комнате"}

        # Проверяем количество участников
        cursor.execute('SELECT COUNT(*) FROM room_members WHERE room_id = ?', (room_id,))
        member_count = cursor.fetchone()[0]

        cursor.execute('SELECT max_players FROM rooms WHERE id = ?', (room_id,))
        max_players_row = cursor.fetchone()
        if not max_players_row:
            raise HTTPException(status_code=404, detail="Комната не найдена")
        max_players = max_players_row[0]

        if member_count >= max_players:
            raise HTTPException(status_code=400, detail="Комната заполнена")

        # Добавляем игрока
        cursor.execute('''
            INSERT INTO room_members (room_id, player_id, is_leader)
            VALUES (?, ?, 0)
        ''', (room_id, player_id))

        conn.commit()
        return {"success": True, "message": "Успешно присоединились к комнате"}
    finally:
        conn.close()

@app.post("/rooms/{room_id}/start")
async def start_game(room_id: int, leader_data: dict):
    """Начало игры (только для лидера)"""
    leader_id = leader_data.get('leader_id')
    
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    try:
        # Проверяем, что пользователь действительно лидер этой комнаты
        cursor.execute('''
            SELECT is_leader FROM room_members 
            WHERE room_id = ? AND player_id = ?
        ''', (room_id, leader_id))
        
        leader_check = cursor.fetchone()
        if not leader_check or not leader_check[0]:
            raise HTTPException(status_code=403, detail="Только лидер может начать игру")
        
        # Проверяем количество участников
        cursor.execute('SELECT COUNT(*) FROM room_members WHERE room_id = ?', (room_id,))
        member_count = cursor.fetchone()[0]
        
        if member_count < 2:
            raise HTTPException(status_code=400, detail="Недостаточно игроков для начала игры (минимум 2)")
        
        if member_count == 3:
            raise HTTPException(status_code=400, detail="Недостаточно игроков для начала игры (нужно 2 или 4)")
        
        # Начинаем игру: помечаем как стартовавшую и убираем из поиска
        cursor.execute('''
            UPDATE rooms SET is_game_started = 1, is_active = 0
            WHERE id = ?
        ''', (room_id,))
        
        conn.commit()
        
        return {
            "message": "Игра успешно начата",
            "room_id": room_id,
            "member_count": member_count,
            "game_type": "1v1" if member_count == 2 else "2v2"
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка начала игры: {str(e)}")
    finally:
        conn.close()

@app.post("/games/")
async def create_game(game: GameCreate):
    """Создание игры"""
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    # Определяем победителя
    winner_team = 1 if game.score_team1 > game.score_team2 else 2
    
    # Создаем запись об игре
    cursor.execute('''
        INSERT INTO games (room_id, score_team1, score_team2, winner_team)
        VALUES (?, ?, ?, ?)
    ''', (game.room_id, game.score_team1, game.score_team2, winner_team))
    
    game_id = cursor.lastrowid
    
    # Завершаем игру
    cursor.execute('UPDATE rooms SET is_game_started = 0 WHERE id = ?', (game.room_id,))
    
    conn.commit()
    conn.close()
    
    return {
        "id": game_id,
        "room_id": game.room_id,
        "score_team1": game.score_team1,
        "score_team2": game.score_team2,
        "winner_team": winner_team
    }

@app.delete("/admin/clear-rooms")
async def clear_all_rooms(admin_id: int = Query(..., description="ID администратора")):
    """Очистка всех комнат (только для администратора)"""
    # Проверяем, что это администратор (ваш Chat ID)
    if admin_id != 972717950:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    
    conn = sqlite3.connect('badminton.db')
    cursor = conn.cursor()
    
    try:
        # Удаляем всех участников комнат
        cursor.execute('DELETE FROM room_members')
        
        # Удаляем все игры
        cursor.execute('DELETE FROM games')
        
        # Удаляем все комнаты
        cursor.execute('DELETE FROM rooms')
        
        conn.commit()
        
        return {"message": "Все комнаты успешно очищены", "deleted_rooms": cursor.rowcount}
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка очистки: {str(e)}")
    finally:
        conn.close()

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
                <p>Система рейтинга по Glicko-2 (SQLite версия)</p>
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
                <h2>🏸 Детали комнаты</h2>
                
                <!-- Информация о комнате -->
                <div class="room-header">
                    <h3 id="room-name-display"></h3>
                    <div class="room-stats">
                        <span class="stat-item">👥 <span id="member-count">0</span>/4</span>
                        <span class="stat-item">👑 Лидер: <span id="room-creator"></span></span>
                    </div>
                </div>
                
                <!-- Разделение на команды -->
                <div class="teams-container">
                    <!-- Левая команда -->
                    <div class="team team-left">
                        <h4>🟦 Команда 1</h4>
                        <div class="team-slots">
                            <div class="player-slot" id="left-slot-1">
                                <div class="slot-placeholder">Пустой слот</div>
                            </div>
                            <div class="player-slot" id="left-slot-2">
                                <div class="slot-placeholder">Пустой слот</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Центральная сетка -->
                    <div class="center-net">
                        <div class="net-icon">🏸</div>
                        <div class="vs-text">VS</div>
                        <div class="net-line"></div>
                    </div>
                    
                    <!-- Правая команда -->
                    <div class="team team-right">
                        <h4>🟥 Команда 2</h4>
                        <div class="team-slots">
                            <div class="player-slot" id="right-slot-1">
                                <div class="slot-placeholder">Пустой слот</div>
                            </div>
                            <div class="player-slot" id="right-slot-2">
                                <div class="slot-placeholder">Пустой слот</div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Список всех участников -->
                <div class="members-section">
                    <h4>📋 Все участники комнаты:</h4>
                    <div class="members-list">
                        <ul id="members-ul"></ul>
                    </div>
                </div>
                
                <!-- Кнопки управления -->
                <div class="room-controls">
                    <!-- Кнопка "Начать игру" только для лидера -->
                    <div id="leader-controls" class="hidden">
                        <button id="start-game-btn" class="btn btn-primary btn-large">
                            🚀 Начать игру
                        </button>
                        <p class="game-rules">Игра начнется когда все слоты будут заполнены</p>
                    </div>
                    
                    <!-- Кнопка "Присоединиться" для обычных пользователей -->
                    <div id="join-controls">
                        <button id="join-room-btn" class="btn btn-secondary">
                            ➕ Присоединиться к комнате
                        </button>
                    </div>
                </div>
                
                <button id="back-to-main-3" class="btn btn-back">← Назад</button>
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
    print("🏸 Запуск Badminton Rating Mini App (SQLite версия)...")
    print("🌐 Сервер будет доступен по адресу: http://localhost:8000")
    print("📱 Mini App будет доступен по адресу: http://localhost:8000/app")
    print("=" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
