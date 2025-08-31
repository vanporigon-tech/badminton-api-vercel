from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple
from datetime import datetime

from models_sqlite import Player, Room, RoomMember, Game, GamePlayer
from schemas import PlayerCreate, RoomCreate, GameCreate

# Player CRUD operations
def get_player_by_telegram_id(db: Session, telegram_id: int) -> Optional[Player]:
    return db.query(Player).filter(Player.telegram_id == telegram_id).first()

def create_player(db: Session, player: PlayerCreate) -> Player:
    db_player = Player(**player.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

def update_player_rating(db: Session, player_id: int, new_rating: float, new_rd: float, new_volatility: float) -> Player:
    player = db.query(Player).filter(Player.id == player_id).first()
    if player:
        player.rating = new_rating
        player.rd = new_rd
        player.volatility = new_volatility
        player.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(player)
    return player

# Room CRUD operations
def create_room(db: Session, room: RoomCreate) -> Room:
    # Get creator information to include in room name
    creator = db.query(Player).filter(Player.id == room.creator_id).first()
    if not creator:
        raise ValueError("Creator not found")
    
    # Create room name with creator's full name
    creator_name = f"{creator.first_name} {creator.last_name}"
    room_name_with_creator = f"{room.name} - {creator_name}"
    
    # Create room with modified name
    room_data = room.dict()
    room_data['name'] = room_name_with_creator
    db_room = Room(**room_data)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    
    # Add creator as first member and leader
    member = RoomMember(
        room_id=db_room.id,
        player_id=room.creator_id,
        is_leader=True
    )
    db.add(member)
    db.commit()
    
    return db_room

def get_room_by_id(db: Session, room_id: int) -> Optional[Room]:
    return db.query(Room).filter(Room.id == room_id).first()

def get_active_rooms(db: Session, skip: int = 0, limit: int = 100) -> List[Room]:
    return db.query(Room).filter(Room.is_active == True).offset(skip).limit(limit).all()

def get_room_with_members(db: Session, room_id: int) -> Optional[Room]:
    return db.query(Room).options(
        joinedload(Room.members).joinedload(RoomMember.player)
    ).filter(Room.id == room_id).first()

def add_player_to_room(db: Session, room_id: int, player_id: int) -> RoomMember:
    # Check if player is already in room
    existing_member = db.query(RoomMember).filter(
        and_(RoomMember.room_id == room_id, RoomMember.player_id == player_id)
    ).first()
    
    if existing_member:
        return existing_member
    
    # Check if room is full
    member_count = db.query(RoomMember).filter(RoomMember.room_id == room_id).count()
    room = get_room_by_id(db, room_id)
    
    if member_count >= room.max_players:
        raise ValueError("Room is full")
    
    member = RoomMember(
        room_id=room_id,
        player_id=player_id,
        is_leader=False
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

def remove_player_from_room(db: Session, room_id: int, player_id: int) -> bool:
    member = db.query(RoomMember).filter(
        and_(RoomMember.room_id == room_id, RoomMember.player_id == player_id)
    ).first()
    
    if member:
        db.delete(member)
        db.commit()
        return True
    return False

def start_game(db: Session, room_id: int) -> bool:
    room = get_room_with_members(db, room_id)
    if not room:
        return False
    
    member_count = len(room.members)
    if member_count < 2:
        return False
    
    room.is_game_started = True
    db.commit()
    return True

