import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT")
)

cur = conn.cursor()

# TIMESTAMPTZ - время хранится в utc, но при select показывается в выбранном часовом поясе
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id bigint PRIMARY KEY,
	faculty text,
    course text,
	gender text,
    name text,
    bio text,
    photo_id text,
    created_at TIMESTAMPTZ DEFAULT now(),
	username text,
    search_gender text,
    status text DEFAULT 'active'
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS interactions (
    user_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    target_id BIGINT NOT NULL REFERENCES users(telegram_id) ON DELETE CASCADE,
    action TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (user_id, target_id)
);
""")

cur.execute("""
CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_target_id ON interactions(target_id);
            
CREATE INDEX IF NOT EXISTS idx_interactions_user_id_created_at ON interactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_interactions_user_target_action ON interactions(user_id, target_id, action);
""")


conn.commit()
cur.close()
conn.close()
print("✅ Таблицы созданы")
