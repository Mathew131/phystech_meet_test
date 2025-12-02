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

print("✅ Подключение успешно")

cur = conn.cursor()

def add_user(telegram_id, username, faculty, course, gender, search_gender, name, bio, photo_id):
    cur.execute(
        """
        INSERT INTO users (telegram_id, username, faculty, course, gender, search_gender, name, bio, photo_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (telegram_id) DO UPDATE SET
            username = EXCLUDED.username,
            faculty = EXCLUDED.faculty,
            course = EXCLUDED.course,
            gender = EXCLUDED.gender,
            search_gender = EXCLUDED.search_gender,
            name = EXCLUDED.name,
            bio = EXCLUDED.bio,
            photo_id = EXCLUDED.photo_id;
        """,
        (telegram_id, username, faculty, course, gender, search_gender, name, bio, photo_id)
    )
    conn.commit()


def turn_off_profile_bd(telegram_id):
    cur.execute(
        """
        UPDATE users
        SET status = 'sleep'
        WHERE telegram_id = %s;
        """,
        (telegram_id,)
    )
    conn.commit()

def turn_on_profile_bd(telegram_id):
    cur.execute(
        """
        UPDATE users
        SET status = 'active'
        WHERE telegram_id = %s;
        """,
        (telegram_id,)
    )
    conn.commit()

def block(telegram_id):
    cur.execute(
        """
        UPDATE users
        SET status = 'block'
        WHERE telegram_id = %s;
        """,
        (telegram_id,)
    )
    conn.commit()

def check_status(telegram_id):
    cur.execute(
        """
        SELECT status
        FROM users
        WHERE telegram_id = %s;
        """,
        (telegram_id,)
    )
    row = cur.fetchone()
    return row[0] if row else None




def get_random_user(user_id: int):
    sql = """
    WITH me AS (
      SELECT gender, search_gender
      FROM users
      WHERE telegram_id = %s
    ),
    candidates AS (
      SELECT u.telegram_id
      FROM users u, me
      WHERE u.telegram_id != %s
        AND u.status = 'active'
        AND (
              me.search_gender = 'Все равно'
              OR (me.search_gender = 'Парни' AND u.gender = 'Парень')
              OR (me.search_gender = 'Девушки' AND u.gender = 'Девушка')
            )
        AND (
              u.search_gender = 'Все равно'
              OR (u.search_gender = 'Парни' AND me.gender = 'Парень')
              OR (u.search_gender = 'Девушки' AND me.gender = 'Девушка')
            )

        AND NOT EXISTS (
          SELECT 1
          FROM interactions i
          WHERE i.user_id = %s AND i.target_id = u.telegram_id
        )
        AND NOT EXISTS (
          SELECT 1
          FROM interactions i
          WHERE i.user_id = u.telegram_id AND i.target_id = %s AND i.action = 'dislike'
        )
    ),

    scored AS (
      SELECT
        c.telegram_id,
        CASE
          WHEN EXISTS (
            SELECT 1 FROM interactions i
            WHERE i.user_id = c.telegram_id AND i.target_id = %s AND i.action = 'like'
          ) THEN 1000000
          ELSE 1
        END AS score
      FROM candidates c
    )

    SELECT telegram_id
    FROM scored
    ORDER BY -LN(RANDOM()) / score
    LIMIT 1;
    """
    cur.execute(sql, (user_id, user_id, user_id, user_id, user_id))
    row = cur.fetchone()
    return row[0] if row else None




def save_action(user_id: int, target_id: int, action: str):
    cur.execute(
        """
        INSERT INTO interactions (user_id, target_id, action)
        VALUES (%s, %s, %s)
        ON CONFLICT (user_id, target_id) DO UPDATE SET
          action = EXCLUDED.action;
        """,
        (user_id, target_id, action)
    )
    conn.commit()

def check_like(first_id: int, second_id: int) -> bool:
    cur.execute(
        """
        SELECT 1
        FROM interactions
        WHERE user_id = %s AND target_id = %s AND action = 'like';
        """,
        (first_id, second_id)
    )
    return cur.fetchone() is not None




def get_name_by_id(user_id: int):
    cur.execute("SELECT name FROM users WHERE telegram_id = %s;", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def get_username_by_id(user_id: int):
    cur.execute("SELECT username FROM users WHERE telegram_id = %s;", (user_id,))
    row = cur.fetchone()
    return row[0] if row else None

def get_user(telegram_id):
    cur.execute("SELECT faculty, course, gender, search_gender, name, bio, photo_id FROM users WHERE telegram_id = %s", (telegram_id,))
    return cur.fetchone()