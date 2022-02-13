import sqlite3

def init_db():
  c = sqlite3.connect('emojimanager.db')
  c.executescript("""
    CREATE TABLE IF NOT EXISTS emojis (
      blob BLOB,
      room TEXT,
      shortcode TEXT PRIMARY KEY NOT NULL,
      mxc TEXT NOT NULL
    );  
    CREATE UNIQUE INDEX IF NOT EXISTS shortcode_room_idx ON emojis (shortcode, room);
    
    CREATE TABLE IF NOT EXISTS rooms (
      room TEXT PRIMARY KEY NOT NULL,
      name TEXT
    );
  """)
  c.close()