import sqlite3

def init_db():
  c = sqlite3.connect('emojimanager.db')
  c.executescript("""
    CREATE TABLE IF NOT EXISTS emojis (
      shortcode TEXT PRIMARY KEY NOT NULL,
      mxc TEXT NOT NULL,
      blob BLOB
    );
    CREATE UNIQUE INDEX IF NOT EXISTS shortcode_idx ON emojis (shortcode);
    CREATE UNIQUE INDEX IF NOT EXISTS mxc_idx ON emojis (mxc);
  """)
  c.close()