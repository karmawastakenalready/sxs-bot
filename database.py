import sqlite3
import os

DB_FILE = "bot.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def setup_database():
    conn = get_connection()
    cursor = conn.cursor()

    # users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            discord_id TEXT PRIMARY KEY,
            ingame_username TEXT,
            game_class TEXT,
            power INTEGER DEFAULT 0,
            power_updated_at TIMESTAMP,
            dm_reminders INTEGER DEFAULT 0
        )
    ''')
    
    # Run safe migrations
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN dm_reminders INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass # Column already exists

    # role_permissions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_permissions (
            guild_id TEXT,
            role_id TEXT,
            permission TEXT,
            PRIMARY KEY (guild_id, role_id, permission)
        )
    ''')

    # guild_config table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guild_config (
            guild_id TEXT PRIMARY KEY,
            reset_time TEXT DEFAULT '00:00',
            reminder_channel_id TEXT,
            announcement_channel_id TEXT,
            announcement_message_id TEXT,
            announcement_text TEXT,
            deputy_role_id TEXT,
            roster_channel_id TEXT,
            roster_message_id TEXT
        )
    ''')

    # guides table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS guides (
            topic TEXT PRIMARY KEY,
            url TEXT,
            description TEXT
        )
    ''')

    # boss_tracker table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS boss_tracker (
            discord_id TEXT PRIMARY KEY,
            date_completed DATE
        )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
    print("Database initialized.")
