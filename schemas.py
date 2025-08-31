from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Player schemas
class PlayerBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    rating: float = Field(default=1500.0, ge=0)
    rd: float = Field(default=350.0, ge=30.0, le=350.0)
    volatility: float = Field(default=0.06, ge=0.01, le=0.1)

class PlayerCreate(PlayerBase):
    telegram_id: int

class PlayerResponse(PlayerBase):
    id: int
    telegram_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Room schemas
class RoomBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    max_players: int = Field(default=4, ge=2, le=4)

class RoomCreate(RoomBase):
    creator_id: int

class RoomResponse(RoomBase):
    id: int
    creator_id: int
    is_active: bool
    is_game_started: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    member_count: int
    creator_name: Optional[str] = None  # Полное имя создателя
    members_names: Optional[List[str]] = None  # Имена всех участников
    
    class Config:
        from_attributes = True

class RoomMemberResponse(BaseModel):
    id: int
    player: PlayerResponse
    joined_at: datetime
    is_leader: bool
    
    class Config:
        from_attributes = True

class RoomDetailResponse(RoomResponse):
    members: List[RoomMemberResponse]
    creator: PlayerResponse
    
    @classmethod
    def from_room(cls, room):
        """Создать RoomDetailResponse из объекта Room с участниками"""
        creator_name = f"{room.creator.first_name} {room.creator.last_name}"
        members_names = [f"{member.player.first_name} {member.player.last_name}" for member in room.members]
        
        return cls(
            id=room.id,
            name=room.name,
            creator_id=room.creator_id,
            max_players=room.max_players,
            is_active=room.is_active,
            is_game_started=room.is_game_started,
            created_at=room.created_at,
            updated_at=room.updated_at,
            member_count=len(room.members),
            creator_name=creator_name,
            members_names=members_names,
            members=room.members,
            creator=room.creator
        )

# Game schemas
class GameCreate(BaseModel):
    room_id: int
    score_team1: int = Field(..., ge=0, le=30)
    score_team2: int = Field(..., ge=0, le=30)

class GameResponse(BaseModel):
    id: int
    room_id: int
    score_team1: int
    score_team2: int
    winner_team: int
    played_at: datetime
    
    class Config:
        from_attributes = True

class GamePlayerResponse(BaseModel):
    id: int
    player: PlayerResponse
    team: int
    rating_before: float
    rating_after: float
    rd_before: float
    rd_after: float
    volatility_before: float
    volatility_after: float
    
    class Config:
        from_attributes = True

class GameDetailResponse(GameResponse):
    players: List[GamePlayerResponse]

# Telegram WebApp schemas
class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    language_code: Optional[str] = None

class TelegramWebApp(BaseModel):
    init_data: str
    user: TelegramUser

# Response schemas
class SuccessResponse(BaseModel):
    success: bool = True
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: str

# Search and filter schemas
class RoomSearchResponse(BaseModel):
    rooms: List[RoomResponse]
    total: int

class PlayerStatsResponse(BaseModel):
    player: PlayerResponse
    games_played: int
    wins: int
    losses: int
    win_rate: float
    current_streak: int
    best_streak: int

