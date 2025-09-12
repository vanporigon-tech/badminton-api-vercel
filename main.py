import os
from fastapi import FastAPI, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, BigInteger, String, DateTime, Boolean, ForeignKey, Float, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка .env
load_dotenv()

# Создание FastAPI приложения
app = FastAPI(
    title="🏸 Badminton Rating API",
    description="API для приложения бадминтон рейтинга",
    version="1.0.0"
)

# CORS настройки (из переменной окружения CORS_ALLOW_ORIGINS, по умолчанию *)
cors_origins_env = os.getenv("CORS_ALLOW_ORIGINS", "*")
if cors_origins_env.strip() == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка базы данных
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/badminton",
)

# Нормализуем URL: postgres:// → postgresql://; используем драйвер psycopg
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
if DATABASE_URL.startswith("postgresql://") and "+" not in DATABASE_URL.split("://", 1)[0]:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модели базы данных
class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    username = Column(String, nullable=True)
    rating = Column(Integer, default=1500)
    rd = Column(Float, default=350.0)
    volatility = Column(Float, default=0.06)
    initial_rank = Column(String, nullable=True)  # 'G'..'A'
    games_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    rooms = relationship("Room", back_populates="creator")
    memberships = relationship("RoomMember", back_populates="player")
    games_played = relationship("GamePlayer", back_populates="player")

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey("players.id"))
    max_players = Column(Integer, default=4)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    # Состояние текущей игры и последний результат (для показа всем участникам)
    current_game = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    last_result = Column(JSON().with_variant(JSONB, 'postgresql'), nullable=True)
    
    # Связи
    creator = relationship("Player", back_populates="rooms")
    members = relationship("RoomMember", back_populates="room")

class RoomMember(Base):
    __tablename__ = "room_members"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    is_leader = Column(Boolean, default=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    room = relationship("Room", back_populates="members")
    player = relationship("Player", back_populates="memberships")


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    games = relationship("Game", back_populates="tournament")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, nullable=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=True)
    score1 = Column(Integer, default=0)
    score2 = Column(Integer, default=0)
    played_at = Column(DateTime, default=datetime.utcnow)

    tournament = relationship("Tournament", back_populates="games")
    players = relationship("GamePlayer", back_populates="game")


class GamePlayer(Base):
    __tablename__ = "game_players"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    team = Column(Integer)  # 1 or 2
    old_rating = Column(Integer)
    new_rating = Column(Integer)
    rating_change = Column(Integer)
    old_rd = Column(Float)
    new_rd = Column(Float)
    old_volatility = Column(Float)
    new_volatility = Column(Float)

    game = relationship("Game", back_populates="players")
    player = relationship("Player", back_populates="games_played")

# Создание таблиц
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Таблицы созданы успешно")
except Exception as e:
    logger.error(f"❌ Ошибка создания таблиц: {e}")

# Безопасный апгрейд типов для telegram_id → BIGINT (если ранние деплои создали INT)
try:
    with engine.connect() as conn:
        # PostgreSQL: изменить тип столбца при необходимости
        conn.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='players' AND column_name='telegram_id' AND data_type='integer'
                ) THEN
                    ALTER TABLE players ALTER COLUMN telegram_id TYPE BIGINT;
                END IF;
                -- Добавляем JSONB поля состояния игры для комнат, если их нет
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='rooms' AND column_name='current_game'
                ) THEN
                    ALTER TABLE rooms ADD COLUMN current_game JSONB;
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name='rooms' AND column_name='last_result'
                ) THEN
                    ALTER TABLE rooms ADD COLUMN last_result JSONB;
                END IF;
            END$$;
        """))
        conn.commit()
        logger.info("✅ Проверка/миграция telegram_id → BIGINT выполнена")
except Exception as e:
    logger.warning(f"⚠️ Не удалось выполнить онлайн-миграцию типов: {e}")

# Dependency для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic модели
class PlayerCreate(BaseModel):
    telegram_id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    initial_rank: Optional[str] = None

class PlayerResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    last_name: Optional[str]
    username: Optional[str]
    rating: int
    rd: float
    volatility: float
    initial_rank: Optional[str]
    games_count: int
    
    class Config:
        from_attributes = True

class RoomCreate(BaseModel):
    name: str
    creator_telegram_id: int
    max_players: int = 4

class RoomMemberResponse(BaseModel):
    id: int
    player: PlayerResponse
    is_leader: bool
    joined_at: datetime
    
    class Config:
        from_attributes = True


class GameCreate(BaseModel):
    team1_telegram_ids: List[int]
    team2_telegram_ids: List[int]
    score1: int
    score2: int
    room_id: Optional[int] = None
    tournament_id: Optional[int] = None


class TournamentCreate(BaseModel):
    name: Optional[str] = None


class TournamentResponse(BaseModel):
    id: int
    name: Optional[str]
    is_active: bool
    created_at: datetime
    ended_at: Optional[datetime]

    class Config:
        from_attributes = True

class StartGameRequest(BaseModel):
    team1_telegram_ids: List[int]
    team2_telegram_ids: List[int]


RANK_TO_RATING: Dict[str, int] = {
    "G": 600,
    "F": 700,
    "E": 800,
    "D": 900,
    "C": 1000,
    "B": 1100,
    "A": 1200,
}

def _ensure_player(db: Session, telegram_id: int, first_name: str = "Игрок", last_name: Optional[str] = None, username: Optional[str] = None) -> Player:
    player = db.query(Player).filter(Player.telegram_id == telegram_id).first()
    if player:
        return player
    player = Player(telegram_id=telegram_id, first_name=first_name or "Игрок", last_name=last_name, username=username)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player

class RoomResponse(BaseModel):
    id: int
    name: str
    creator_id: int
    creator_full_name: str
    max_players: int
    member_count: int
    is_active: bool
    created_at: datetime
    members: List[RoomMemberResponse] = []
    current_game: Optional[Dict] = None
    last_result: Optional[Dict] = None
    
    class Config:
        from_attributes = True

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "🏸 Badminton Rating API", 
        "version": "1.0.0",
        "status": "active"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/players/", response_model=PlayerResponse)
async def create_or_get_player(player: PlayerCreate, db: Session = Depends(get_db)):
    """Создает или получает игрока по telegram_id"""
    try:
        # Проверяем, существует ли игрок
        existing_player = db.query(Player).filter(Player.telegram_id == player.telegram_id).first()
        
        if existing_player:
            # Обновляем данные если они изменились
            existing_player.first_name = player.first_name
            if player.last_name:
                existing_player.last_name = player.last_name
            if player.username:
                existing_player.username = player.username
            if player.initial_rank and not existing_player.initial_rank:
                existing_player.initial_rank = player.initial_rank
                if player.initial_rank in RANK_TO_RATING and existing_player.rating == 1500:
                    existing_player.rating = RANK_TO_RATING[player.initial_rank]
            db.commit()
            db.refresh(existing_player)
            return existing_player
        
        # Создаем нового игрока
        initial_data = player.dict()
        init_rank = initial_data.pop("initial_rank", None)
        new_player = Player(**initial_data)
        if init_rank:
            new_player.initial_rank = init_rank
            if init_rank in RANK_TO_RATING:
                new_player.rating = RANK_TO_RATING[init_rank]
        db.add(new_player)
        db.commit()
        db.refresh(new_player)
        
        logger.info(f"✅ Создан новый игрок: {new_player.first_name} (ID: {new_player.telegram_id})")
        return new_player
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания игрока: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/players/set_rank", response_model=PlayerResponse)
async def set_player_rank(data: PlayerCreate, db: Session = Depends(get_db), force: bool = False):
    """Установить начальный ранг игрока (G..A) и применить стартовый рейтинг, если не был установлен ранее."""
    try:
        player = db.query(Player).filter(Player.telegram_id == data.telegram_id).first()
        if not player:
            player = _ensure_player(db, data.telegram_id, data.first_name, data.last_name, data.username)
        if data.initial_rank:
            player.initial_rank = data.initial_rank
            if force or player.games_count == 0 or player.rating in (None, 0, 1500):
                mapped = RANK_TO_RATING.get(data.initial_rank)
                if mapped:
                    player.rating = mapped
        db.commit()
        db.refresh(player)
        return player
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/players/{telegram_id}", response_model=PlayerResponse)
async def get_player(telegram_id: int, db: Session = Depends(get_db)):
    """Получает игрока по telegram_id"""
    player = db.query(Player).filter(Player.telegram_id == telegram_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    return player

@app.post("/rooms/", response_model=RoomResponse)
async def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    """Создает новую комнату"""
    try:
        # Находим игрока-создателя
        creator = db.query(Player).filter(Player.telegram_id == room.creator_telegram_id).first()
        if not creator:
            # Автосоздание игрока, чтобы фронту не делать лишний вызов
            creator = _ensure_player(db, room.creator_telegram_id)
        # Ограничение: один активный рум на пользователя
        existing_active = db.query(Room).filter(Room.creator_id == creator.id, Room.is_active == True).first()
        if existing_active:
            # Возвращаем уже существующую комнату
            members = db.query(RoomMember).filter(RoomMember.room_id == existing_active.id).all()
            creator_full_name = f"{creator.first_name} {creator.last_name or ''}".strip()
            return RoomResponse(
                id=existing_active.id,
                name=existing_active.name,
                creator_id=existing_active.creator_id,
                creator_full_name=creator_full_name,
                max_players=existing_active.max_players,
                member_count=len(members),
                is_active=existing_active.is_active,
                created_at=existing_active.created_at,
                members=[
                    RoomMemberResponse(
                        id=m.id,
                        player=m.player,
                        is_leader=m.is_leader,
                        joined_at=m.joined_at
                    ) for m in members
                ]
            )

        # Создаем комнату
        new_room = Room(
            name=room.name,
            creator_id=creator.id,
            max_players=room.max_players
        )
        db.add(new_room)
        db.commit()
        db.refresh(new_room)
        
        # Добавляем создателя как участника и лидера
        room_member = RoomMember(
            room_id=new_room.id,
            player_id=creator.id,
            is_leader=True
        )
        db.add(room_member)
        db.commit()
        
        # Формируем ответ
        creator_full_name = f"{creator.first_name} {creator.last_name or ''}".strip()
        
        result = RoomResponse(
            id=new_room.id,
            name=new_room.name,
            creator_id=new_room.creator_id,
            creator_full_name=creator_full_name,
            max_players=new_room.max_players,
            member_count=1,
            is_active=new_room.is_active,
            created_at=new_room.created_at,
            members=[RoomMemberResponse(
                id=room_member.id,
                player=creator,
                is_leader=True,
                joined_at=room_member.joined_at
            )]
        )
        
        logger.info(f"✅ Создана комната: {new_room.name} (ID: {new_room.id})")
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка создания комнаты: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _calculate_and_apply_ratings(db: Session, team1: List[Player], team2: List[Player], score1: int, score2: int):
    from glicko2 import glicko2, calculate_team_rating, distribute_rating_changes

    # Build team stats
    team1_stats = [(p.rating, p.rd, p.volatility) for p in team1]
    team2_stats = [(p.rating, p.rd, p.volatility) for p in team2]

    t1_rating, t1_rd, t1_vol = calculate_team_rating(team1_stats)
    t2_rating, t2_rd, t2_vol = calculate_team_rating(team2_stats)

    # Scores
    if score1 > score2:
        s1, s2 = 1.0, 0.0
    elif score2 > score1:
        s1, s2 = 0.0, 1.0
    else:
        s1, s2 = 0.5, 0.5

    # Update team ratings vs each other
    new_t1_rating, new_t1_rd, new_t1_vol = glicko2.calculate_new_rating(
        t1_rating, t1_rd, t1_vol, [t2_rating], [t2_rd], [s1]
    )
    new_t2_rating, new_t2_rd, new_t2_vol = glicko2.calculate_new_rating(
        t2_rating, t2_rd, t2_vol, [t1_rating], [t1_rd], [s2]
    )

    # Distribute changes back to players
    team1_new = distribute_rating_changes(
        team1_stats, new_t1_rating - t1_rating, new_t1_rd - t1_rd, new_t1_vol - t1_vol
    )
    team2_new = distribute_rating_changes(
        team2_stats, new_t2_rating - t2_rating, new_t2_rd - t2_rd, new_t2_vol - t2_vol
    )

    # Apply and collect changes
    changes: Dict[int, Dict] = {}
    for player, (nr, nrd, nvol) in zip(team1, team1_new):
        old = player.rating
        proposed = int(round(nr))
        delta = proposed - old
        # Safety clamp to avoid absurd jumps due to numerical instability or bad inputs
        if abs(delta) > 100:
            logger.warning(f"⚠️ Clamping rating jump for {player.telegram_id}: {delta} → {max(-100, min(100, delta))}")
            delta = max(-100, min(100, delta))
            proposed = old + delta
        player.rating = proposed
        changes[player.telegram_id] = {
            "old_rating": old,
            "new_rating": player.rating,
            "rating_change": player.rating - old,
            "team": 1,
            "won": score1 > score2,
        }
        player.rd = float(nrd)
        player.volatility = float(nvol)
        player.games_count = (player.games_count or 0) + 1

    for player, (nr, nrd, nvol) in zip(team2, team2_new):
        old = player.rating
        proposed = int(round(nr))
        delta = proposed - old
        if abs(delta) > 100:
            logger.warning(f"⚠️ Clamping rating jump for {player.telegram_id}: {delta} → {max(-100, min(100, delta))}")
            delta = max(-100, min(100, delta))
            proposed = old + delta
        player.rating = proposed
        changes[player.telegram_id] = {
            "old_rating": old,
            "new_rating": player.rating,
            "rating_change": player.rating - old,
            "team": 2,
            "won": score2 > score1,
        }
        player.rd = float(nrd)
        player.volatility = float(nvol)
        player.games_count = (player.games_count or 0) + 1

    return changes


@app.post("/games")
async def create_game(game: GameCreate, db: Session = Depends(get_db)):
    """Создать игру, обновить рейтинги Glicko-2, вернуть изменения для UI."""
    try:
        # Ensure players
        team1 = [
            _ensure_player(db, pid) for pid in game.team1_telegram_ids
        ]
        team2 = [
            _ensure_player(db, pid) for pid in game.team2_telegram_ids
        ]

        # Calculate ratings (strict, no fallback ±10)
        changes = _calculate_and_apply_ratings(db, team1, team2, game.score1, game.score2)

        # Persist Game and per-player entries
        new_game = Game(
            room_id=game.room_id,
            tournament_id=game.tournament_id,
            score1=game.score1,
            score2=game.score2,
        )
        db.add(new_game)
        db.commit()
        db.refresh(new_game)

        for p in team1:
            ch = changes[p.telegram_id]
            gp = GamePlayer(
                game_id=new_game.id,
                player_id=p.id,
                team=1,
                old_rating=ch["old_rating"],
                new_rating=ch["new_rating"],
                rating_change=ch["rating_change"],
                old_rd=0.0,
                new_rd=p.rd,
                old_volatility=0.0,
                new_volatility=p.volatility,
            )
            db.add(gp)

        for p in team2:
            ch = changes[p.telegram_id]
            gp = GamePlayer(
                game_id=new_game.id,
                player_id=p.id,
                team=2,
                old_rating=ch["old_rating"],
                new_rating=ch["new_rating"],
                rating_change=ch["rating_change"],
                old_rd=0.0,
                new_rd=p.rd,
                old_volatility=0.0,
                new_volatility=p.volatility,
            )
            db.add(gp)

        db.commit()

        # Update Google Users sheet
        try:
            from google_sheets import update_users_sheet

            # Export minimal users data
            users = [
                {
                    "telegram_id": p.telegram_id,
                    "name": f"{p.first_name} {p.last_name or ''}".strip(),
                    "username": p.username,
                    "games_played": p.games_count or 0,
                    "rating": p.rating,
                }
                for p in db.query(Player).all()
            ]
            update_users_sheet(users)
        except Exception:
            pass

        # Обновляем состояние комнаты, чтобы все участники увидели результат
        if game.room_id:
            room = db.query(Room).filter(Room.id == game.room_id).first()
            if room:
                room.last_result = {
                    "game_id": new_game.id,
                    "score1": game.score1,
                    "score2": game.score2,
                    "rating_changes": changes,
                    "finished_at": datetime.utcnow().isoformat()
                }
                room.current_game = None
                db.add(room)
                db.commit()

        return {"game_id": new_game.id, "rating_changes": changes}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tournaments/start", response_model=TournamentResponse)
async def start_tournament(data: TournamentCreate, db: Session = Depends(get_db)):
    t = Tournament(name=data.name or f"Tournament {datetime.utcnow().strftime('%Y-%m-%d')}")
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


@app.post("/tournaments/{tournament_id}/end")
async def end_tournament(tournament_id: int, db: Session = Depends(get_db)):
    t = db.query(Tournament).filter(Tournament.id == tournament_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Турнир не найден")
    t.is_active = False
    t.ended_at = datetime.utcnow()
    db.commit()

    # Build games structure for sheets
    games = db.query(Game).filter(Game.tournament_id == t.id).all()
    players_stats: Dict[int, Dict] = {}
    # Aggregate stats from GamePlayer
    for g in games:
        gp_list = db.query(GamePlayer).filter(GamePlayer.game_id == g.id).all()
        for gp in gp_list:
            pid = gp.player_id
            p = db.query(Player).filter(Player.id == pid).first()
            tid = p.telegram_id
            if tid not in players_stats:
                players_stats[tid] = {
                    "id": tid,
                    "games_played": 0,
                    "games_won": 0,
                    "points_for": 0,
                    "points_against": 0,
                    "rating_change": 0,
                    "old_rating": gp.old_rating,
                    "new_rating": gp.new_rating,
                }
            ps = players_stats[tid]
            ps["games_played"] += 1
            won = (g.score1 > g.score2 and gp.team == 1) or (g.score2 > g.score1 and gp.team == 2)
            if won:
                ps["games_won"] += 1
            if gp.team == 1:
                ps["points_for"] += g.score1
                ps["points_against"] += g.score2
            else:
                ps["points_for"] += g.score2
                ps["points_against"] += g.score1
            ps["rating_change"] += gp.rating_change
            ps["new_rating"] = gp.new_rating

    # Compose tournament_data format for sheets lib
    tournament_data = {
        "games": [
            {
                "team1": [
                    db.query(Player).filter(Player.id == gp.player_id).first().telegram_id
                    for gp in db.query(GamePlayer).filter(GamePlayer.game_id == g.id, GamePlayer.team == 1).all()
                ],
                "team2": [
                    db.query(Player).filter(Player.id == gp.player_id).first().telegram_id
                    for gp in db.query(GamePlayer).filter(GamePlayer.game_id == g.id, GamePlayer.team == 2).all()
                ],
                "score1": g.score1,
                "score2": g.score2,
                "played_at": g.played_at.isoformat(),
            }
            for g in games
        ]
    }

    try:
        from google_sheets import create_tournament_table
        url = create_tournament_table(t.id, tournament_data)
    except Exception as e:
        url = None

    return {"tournament_id": t.id, "sheet_url": url}


@app.get("/tournaments/active", response_model=TournamentResponse)
async def get_active_tournament(db: Session = Depends(get_db)):
    """Возвращает единственный активный турнир (если есть)."""
    t = db.query(Tournament).filter(Tournament.is_active == True).order_by(Tournament.created_at.desc()).first()
    if not t:
        raise HTTPException(status_code=404, detail="Активный турнир не найден")
    return t


@app.post("/tournaments/end_latest")
async def end_latest_tournament(db: Session = Depends(get_db)):
    """Завершает последний активный турнир и создаёт таблицу. Используется ботом, если турнир один."""
    t = db.query(Tournament).filter(Tournament.is_active == True).order_by(Tournament.created_at.desc()).first()
    if not t:
        raise HTTPException(status_code=404, detail="Активный турнир не найден")
    t.is_active = False
    t.ended_at = datetime.utcnow()
    db.commit()

    games = db.query(Game).filter(Game.tournament_id == t.id).all()
    tournament_data = {
        "games": [
            {
                "team1": [
                    db.query(Player).filter(Player.id == gp.player_id).first().telegram_id
                    for gp in db.query(GamePlayer).filter(GamePlayer.game_id == g.id, GamePlayer.team == 1).all()
                ],
                "team2": [
                    db.query(Player).filter(Player.id == gp.player_id).first().telegram_id
                    for gp in db.query(GamePlayer).filter(GamePlayer.game_id == g.id, GamePlayer.team == 2).all()
                ],
                "score1": g.score1,
                "score2": g.score2,
                "played_at": g.played_at.isoformat(),
            }
            for g in games
        ]
    }

    try:
        from google_sheets import create_tournament_table
        url = create_tournament_table(t.id, tournament_data)
    except Exception:
        url = None
    return {"tournament_id": t.id, "sheet_url": url}

@app.get("/rooms/", response_model=List[RoomResponse])
async def get_rooms(response: Response, db: Session = Depends(get_db)):
    """Получает список всех активных комнат"""
    try:
        rooms = db.query(Room).filter(Room.is_active == True).all()
        
        # Отключаем кэширование списков комнат
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        result = []
        for room in rooms:
            # Получаем всех участников комнаты
            members = db.query(RoomMember).filter(RoomMember.room_id == room.id).all()
            
            # Формируем полное имя создателя
            creator_full_name = f"{room.creator.first_name} {room.creator.last_name or ''}".strip()
            
            room_response = RoomResponse(
                id=room.id,
                name=room.name,
                creator_id=room.creator_id,
                creator_full_name=creator_full_name,
                max_players=room.max_players,
                member_count=len(members),
                is_active=room.is_active,
                created_at=room.created_at,
                members=[
                    RoomMemberResponse(
                        id=member.id,
                        player=member.player,
                        is_leader=member.is_leader,
                        joined_at=member.joined_at
                    ) for member in members
                ]
            )
            result.append(room_response)
        
        logger.info(f"✅ Найдено комнат: {len(result)}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения комнат: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/rooms/clear_all")
async def clear_all_rooms(db: Session = Depends(get_db)):
    """Админский эндпоинт: удаляет все комнаты и участников."""
    try:
        count_members = db.query(RoomMember).delete()
        count_rooms = db.query(Room).delete()
        db.commit()
        logger.info(f"✅ Очистка комнат: rooms={count_rooms}, members={count_members}")
        return {"rooms_deleted": count_rooms, "members_deleted": count_members}
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Ошибка очистки комнат: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(room_id: int, response: Response, db: Session = Depends(get_db)):
    """Получает детали комнаты по ID"""
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Комната не найдена")
        
        # Получаем всех участников комнаты
        members = db.query(RoomMember).filter(RoomMember.room_id == room_id).all()
        
        # Формируем полное имя создателя
        creator_full_name = f"{room.creator.first_name} {room.creator.last_name or ''}".strip()
        
        # Отключаем кэширование деталей комнаты
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        result = RoomResponse(
            id=room.id,
            name=room.name,
            creator_id=room.creator_id,
            creator_full_name=creator_full_name,
            max_players=room.max_players,
            member_count=len(members),
            is_active=room.is_active,
            created_at=room.created_at,
            members=[
                RoomMemberResponse(
                    id=member.id,
                    player=member.player,
                    is_leader=member.is_leader,
                    joined_at=member.joined_at
                ) for member in members
            ],
            current_game=room.current_game,
            last_result=room.last_result
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения комнаты {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rooms/{room_id}/join", response_model=RoomResponse)
async def join_room(room_id: int, telegram_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    player = db.query(Player).filter(Player.telegram_id == telegram_id).first()
    if not player:
        player = _ensure_player(db, telegram_id)
    # Check membership
    exists = db.query(RoomMember).filter(RoomMember.room_id == room_id, RoomMember.player_id == player.id).first()
    if exists:
        pass
    else:
        # Limit by max_players
        count = db.query(RoomMember).filter(RoomMember.room_id == room_id).count()
        if count >= room.max_players:
            raise HTTPException(status_code=400, detail="Комната заполнена")
        db.add(RoomMember(room_id=room_id, player_id=player.id, is_leader=False))
        db.commit()

    return await get_room(room_id, db)


@app.post("/rooms/{room_id}/leave", response_model=RoomResponse)
async def leave_room(room_id: int, telegram_id: int, db: Session = Depends(get_db)):
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена")
    player = db.query(Player).filter(Player.telegram_id == telegram_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Игрок не найден")
    membership = db.query(RoomMember).filter(RoomMember.room_id == room_id, RoomMember.player_id == player.id).first()
    if not membership:
        # Если участник не найден, но это создатель — удаляем комнату (случай рассинхрона ID)
        if room.creator and room.creator.telegram_id == telegram_id:
            db.query(RoomMember).filter(RoomMember.room_id == room_id).delete()
            # Ответ до удаления комнаты
            response = RoomResponse(
                id=room.id,
                name=room.name,
                creator_id=room.creator_id,
                creator_full_name=f"{room.creator.first_name} {room.creator.last_name or ''}".strip(),
                max_players=room.max_players,
                member_count=0,
                is_active=False,
                created_at=room.created_at,
                members=[]
            )
            db.delete(room)
            db.commit()
            return response
        # Иначе — возвращаем текущее состояние без изменений
        return await get_room(room_id, db)
    is_leader = bool(membership.is_leader)
    # Удаляем участника
    db.delete(membership)
    db.commit()
    if is_leader:
        # Если вышел лидер — расформировываем комнату (удаляем всех участников и саму комнату),
        # чтобы она гарантированно не появлялась в поиске
        db.query(RoomMember).filter(RoomMember.room_id == room_id).delete()
        # Подготовим ответ до удаления комнаты
        response = RoomResponse(
            id=room.id,
            name=room.name,
            creator_id=room.creator_id,
            creator_full_name=f"{room.creator.first_name} {room.creator.last_name or ''}".strip(),
            max_players=room.max_players,
            member_count=0,
            is_active=False,
            created_at=room.created_at,
            members=[]
        )
        # Удаляем комнату целиком
        db.delete(room)
        db.commit()
        return response
    # Возвращаем обновлённую комнату
    return await get_room(room_id, db)


@app.post("/rooms/{room_id}/start_game", response_model=RoomResponse)
async def start_game(room_id: int, req: StartGameRequest, db: Session = Depends(get_db)):
    """Помечает старт игры в комнате, чтобы все участники увидели."""
    room = db.query(Room).filter(Room.id == room_id, Room.is_active == True).first()
    if not room:
        raise HTTPException(status_code=404, detail="Комната не найдена или неактивна")
    room.current_game = {
        "started": True,
        "team1": req.team1_telegram_ids,
        "team2": req.team2_telegram_ids,
        "started_at": datetime.utcnow().isoformat()
    }
    room.last_result = None
    # Убираем комнату из поиска сразу после старта игры
    room.is_active = False
    db.add(room)
    db.commit()
    return await get_room(room_id, db)

@app.delete("/rooms/{room_id}")
async def delete_room(room_id: int, db: Session = Depends(get_db)):
    """Удаляет комнату"""
    try:
        room = db.query(Room).filter(Room.id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Комната не найдена")
        
        # Удаляем всех участников
        db.query(RoomMember).filter(RoomMember.room_id == room_id).delete()
        
        # Удаляем комнату
        db.delete(room)
        db.commit()
        
        logger.info(f"✅ Комната {room_id} удалена")
        return {"message": "Комната успешно удалена"}
        
    except Exception as e:
        logger.error(f"❌ Ошибка удаления комнаты {room_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Для совместимости с Vercel
def handler(request, context):
    return app(request, context)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
