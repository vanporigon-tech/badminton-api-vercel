from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Player(Base):
    __tablename__ = "players"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    rating = Column(Float, default=1500.0)  # Glicko-2 rating
    rd = Column(Float, default=350.0)       # Glicko-2 rating deviation
    volatility = Column(Float, default=0.06) # Glicko-2 volatility
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    room_memberships = relationship("RoomMember", back_populates="player")
    games_played = relationship("GamePlayer", back_populates="player")

class Room(Base):
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    creator_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    max_players = Column(Integer, default=4)
    is_active = Column(Boolean, default=True)
    is_game_started = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("Player")
    members = relationship("RoomMember", back_populates="room")
    games = relationship("Game", back_populates="room")

class RoomMember(Base):
    __tablename__ = "room_members"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_leader = Column(Boolean, default=False)
    
    # Relationships
    room = relationship("Room", back_populates="members")
    player = relationship("Player", back_populates="room_memberships")

class Game(Base):
    __tablename__ = "games"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    score_team1 = Column(Integer, nullable=False)
    score_team2 = Column(Integer, nullable=False)
    winner_team = Column(Integer, nullable=False)  # 1 or 2
    played_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    room = relationship("Room", back_populates="games")
    players = relationship("GamePlayer", back_populates="game")

class GamePlayer(Base):
    __tablename__ = "game_players"
    
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"), nullable=False)
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False)
    team = Column(Integer, nullable=False)  # 1 or 2
    rating_before = Column(Float, nullable=False)
    rating_after = Column(Float, nullable=False)
    rd_before = Column(Float, nullable=False)
    rd_after = Column(Float, nullable=False)
    volatility_before = Column(Float, nullable=False)
    volatility_after = Column(Float, nullable=False)
    
    # Relationships
    game = relationship("Game", back_populates="players")
    player = relationship("Player", back_populates="games_played")

