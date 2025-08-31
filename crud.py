from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple
from datetime import datetime

from models import Player, Room, RoomMember, Game, GamePlayer
from schemas import PlayerCreate, RoomCreate, GameCreate
from glicko2 import calculate_team_rating, distribute_rating_changes, glicko2

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
    db_room = Room(**room.dict())
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

# Game CRUD operations
def create_game(db: Session, game: GameCreate) -> Game:
    # Determine winner
    if game.score_team1 > game.score_team2:
        winner_team = 1
    elif game.score_team2 > game.score_team1:
        winner_team = 2
    else:
        winner_team = 1  # Default to team 1 in case of tie
    
    db_game = Game(
        room_id=game.room_id,
        score_team1=game.score_team1,
        score_team2=game.score_team2,
        winner_team=winner_team
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    
    return db_game

def calculate_game_ratings(db: Session, game_id: int) -> bool:
    """Calculate new ratings for all players in a game"""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        return False
    
    room = get_room_with_members(db, game.room_id)
    if not room:
        return False
    
    members = room.members
    if len(members) < 2:
        return False
    
    # Get current ratings for all players
    player_ratings = []
    for member in members:
        player = member.player
        player_ratings.append((
            player.id,
            player.rating,
            player.rd,
            player.volatility
        ))
    
    # For 4 players, create 2 teams
    if len(members) == 4:
        # Create teams (first 2 vs last 2)
        team1_players = player_ratings[:2]
        team2_players = player_ratings[2:]
        
        # Calculate team ratings
        team1_rating, team1_rd, team1_vol = calculate_team_rating(team1_players)
        team2_rating, team2_rd, team2_vol = calculate_team_rating(team2_players)
        
        # Calculate new team ratings using Glicko-2
        if game.winner_team == 1:
            team1_score = 1.0
            team2_score = 0.0
        else:
            team1_score = 0.0
            team2_score = 1.0
        
        new_team1_rating, new_team1_rd, new_team1_vol = glicko2.calculate_new_rating(
            team1_rating, team1_rd, team1_vol,
            [team2_rating], [team2_rd], [team2_score]
        )
        
        new_team2_rating, new_team2_rd, new_team2_vol = glicko2.calculate_new_rating(
            team2_rating, team2_rd, team2_vol,
            [team1_rating], [team1_rd], [team1_score]
        )
        
        # Distribute changes back to individual players
        team1_changes = (
            new_team1_rating - team1_rating,
            new_team1_rd - team1_rd,
            new_team1_vol - team1_vol
        )
        team2_changes = (
            new_team2_rating - team2_rating,
            new_team2_rd - team2_rd,
            new_team2_vol - team2_vol
        )
        
        new_team1_players = distribute_rating_changes(team1_players, *team1_changes)
        new_team2_players = distribute_rating_changes(team2_players, *team2_changes)
        
        # Update all players
        all_new_ratings = new_team1_players + new_team2_players
        
    elif len(members) == 2:
        # 1v1 game
        player1 = player_ratings[0]
        player2 = player_ratings[1]
        
        if game.winner_team == 1:
            player1_score = 1.0
            player2_score = 0.0
        else:
            player1_score = 0.0
            player2_score = 1.0
        
        new_player1_rating, new_player1_rd, new_player1_vol = glicko2.calculate_new_rating(
            player1[1], player1[2], player1[3],
            [player2[1]], [player2[2]], [player2_score]
        )
        
        new_player2_rating, new_player2_rd, new_player2_vol = glicko2.calculate_new_rating(
            player2[1], player2[2], player2[3],
            [player1[1]], [player1[2]], [player1_score]
        )
        
        all_new_ratings = [
            (player1[0], new_player1_rating, new_player1_rd, new_player1_vol),
            (player2[0], new_player2_rating, new_player2_rd, new_player2_vol)
        ]
    
    else:
        # Invalid number of players
        return False
    
    # Create game player records and update ratings
    for i, (player_id, new_rating, new_rd, new_vol) in enumerate(all_new_ratings):
        # Get old ratings
        old_player = db.query(Player).filter(Player.id == player_id).first()
        if not old_player:
            continue
        
        # Determine team (1 or 2)
        team = 1 if i < len(all_new_ratings) // 2 else 2
        
        # Create game player record
        game_player = GamePlayer(
            game_id=game_id,
            player_id=player_id,
            team=team,
            rating_before=old_player.rating,
            rating_after=new_rating,
            rd_before=old_player.rd,
            rd_after=new_rd,
            volatility_before=old_player.volatility,
            volatility_after=new_vol
        )
        db.add(game_player)
        
        # Update player rating
        old_player.rating = new_rating
        old_player.rd = new_rd
        old_player.volatility = new_vol
        old_player.updated_at = datetime.utcnow()
    
    db.commit()
    return True

def get_player_games(db: Session, player_id: int, skip: int = 0, limit: int = 50) -> List[Game]:
    return db.query(Game).join(GamePlayer).filter(
        GamePlayer.player_id == player_id
    ).order_by(Game.played_at.desc()).offset(skip).limit(limit).all()

def get_player_stats(db: Session, player_id: int) -> dict:
    """Get player statistics"""
    games = get_player_games(db, player_id)
    
    wins = 0
    losses = 0
    current_streak = 0
    best_streak = 0
    temp_streak = 0
    
    for game in games:
        game_player = db.query(GamePlayer).filter(
            and_(GamePlayer.game_id == game.id, GamePlayer.player_id == player_id)
        ).first()
        
        if game_player:
            if (game.winner_team == game_player.team):
                wins += 1
                temp_streak += 1
                current_streak = max(current_streak, temp_streak)
            else:
                losses += 1
                temp_streak = 0
                best_streak = max(best_streak, current_streak)
                current_streak = 0
    
    total_games = wins + losses
    win_rate = (wins / total_games * 100) if total_games > 0 else 0
    
    return {
        "games_played": total_games,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "current_streak": current_streak,
        "best_streak": best_streak
    }

