import sqlite3

def init_db():
  c = sqlite3.connect('emojimanager.db')
  c.executescript("""
    CREATE TABLE IF NOT EXISTS emojis (
      blob BLOB,
      room TEXT,
      shortcode TEXT NOT NULL,
      mxc TEXT NOT NULL
    );  
    CREATE UNIQUE INDEX IF NOT EXISTS shortcode_room_idx ON emojis (shortcode, room);
    CREATE UNIQUE INDEX IF NOT EXISTS shortcode_idx ON emojis (shortcode);
    
    CREATE TABLE IF NOT EXISTS rooms (
      room TEXT PRIMARY KEY NOT NULL,
      userid TEXT NOT NULL,
      name TEXT
    );
    CREATE UNIQUE INDEX IF NOT EXISTS room_name_idx ON rooms (room, name);
    
    CREATE TABLE IF NOT EXISTS users (
      userid TEXT PRIMARY KEY NOT NULL,
      homeserver TEXT NOT NULL,
      token TEXT
    );
  """)
  c.close()