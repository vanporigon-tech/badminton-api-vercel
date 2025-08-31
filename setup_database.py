#!/usr/bin/env python3
"""
Database setup script for Badminton Rating Mini App
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """Create database if it doesn't exist"""
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database='postgres'  # Connect to default database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", 
                      (os.getenv('DB_NAME', 'badminton_rating'),))
        exists = cursor.fetchone()
        
        if not exists:
            # Create database
            cursor.execute(f"CREATE DATABASE {os.getenv('DB_NAME', 'badminton_rating')}")
            print(f"✅ Database '{os.getenv('DB_NAME', 'badminton_rating')}' created successfully!")
        else:
            print(f"✅ Database '{os.getenv('DB_NAME', 'badminton_rating')}' already exists!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def create_tables():
    """Create all tables in the database"""
    try:
        # Connect to our database
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            database=os.getenv('DB_NAME', 'badminton_rating')
        )
        cursor = conn.cursor()
        
        # Create tables
        tables = [
            """
            CREATE TABLE IF NOT EXISTS players (
                id SERIAL PRIMARY KEY,
                telegram_id INTEGER UNIQUE NOT NULL,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                rating FLOAT DEFAULT 1500.0,
                rd FLOAT DEFAULT 350.0,
                volatility FLOAT DEFAULT 0.06,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id SERIAL PRIMARY KEY,
                name VARCHAR(200) NOT NULL,
                creator_id INTEGER REFERENCES players(id),
                max_players INTEGER DEFAULT 4,
                is_active BOOLEAN DEFAULT TRUE,
                is_game_started BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS room_members (
                id SERIAL PRIMARY KEY,
                room_id INTEGER REFERENCES rooms(id) ON DELETE CASCADE,
                player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
                joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_leader BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                room_id INTEGER REFERENCES rooms(id),
                score_team1 INTEGER NOT NULL,
                score_team2 INTEGER NOT NULL,
                winner_team INTEGER NOT NULL,
                played_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS game_players (
                id SERIAL PRIMARY KEY,
                game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
                player_id INTEGER REFERENCES players(id),
                team INTEGER NOT NULL,
                rating_before FLOAT NOT NULL,
                rating_after FLOAT NOT NULL,
                rd_before FLOAT NOT NULL,
                rd_after FLOAT NOT NULL,
                volatility_before FLOAT NOT NULL,
                volatility_after FLOAT NOT NULL
            )
            """
        ]
        
        for table_sql in tables:
            cursor.execute(table_sql)
            print(f"✅ Table created/verified successfully!")
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_players_telegram_id ON players(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_rooms_creator_id ON rooms(creator_id)",
            "CREATE INDEX IF NOT EXISTS idx_room_members_room_id ON room_members(room_id)",
            "CREATE INDEX IF NOT EXISTS idx_room_members_player_id ON room_members(player_id)",
            "CREATE INDEX IF NOT EXISTS idx_games_room_id ON games(room_id)",
            "CREATE INDEX IF NOT EXISTS idx_game_players_game_id ON game_players(game_id)",
            "CREATE INDEX IF NOT EXISTS idx_game_players_player_id ON game_players(player_id)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            print(f"✅ Index created/verified successfully!")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ All tables and indexes created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def main():
    """Main setup function"""
    print("🏸 Setting up Badminton Rating Database...")
    print("=" * 50)
    
    # Check environment variables
    required_vars = ['DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with the required variables.")
        return False
    
    print(f"📊 Database Host: {os.getenv('DB_HOST')}")
    print(f"📊 Database Port: {os.getenv('DB_PORT')}")
    print(f"📊 Database Name: {os.getenv('DB_NAME')}")
    print(f"📊 Database User: {os.getenv('DB_USER')}")
    print("=" * 50)
    
    # Create database
    if not create_database():
        return False
    
    # Create tables
    if not create_tables():
        return False
    
    print("=" * 50)
    print("🎉 Database setup completed successfully!")
    print("You can now run the application with: python main.py")
    return True

if __name__ == "__main__":
    main()

