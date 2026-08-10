import os
import json

from config import DATA_FILE

DATABASE_URL = os.environ.get("DATABASE_URL")


def load_json_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"menu": [], "orders": []}


def save_json_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_connection():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price INTEGER NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id BIGINT PRIMARY KEY,
                data JSONB NOT NULL
            )
        """)

        conn.commit()
        cur.close()
    finally:
        conn.close()


def load_data():
    if not DATABASE_URL:
        return load_json_data()

    init_db()
    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT id, name, price
            FROM menu
            ORDER BY id
        """)

        menu = [
            {
                "id": row[0],
                "name": row[1],
                "price": row[2]
            }
            for row in cur.fetchall()
        ]

        cur.execute("""
            SELECT data
            FROM orders
            ORDER BY id
        """)

        orders = [row[0] for row in cur.fetchall()]

        cur.close()

        return {
            "menu": menu,
            "orders": orders
        }
    finally:
        conn.close()


def save_data(data):
    if not DATABASE_URL:
        save_json_data(data)
        return

    init_db()
    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute("DELETE FROM menu")

        for item in data.get("menu", []):
            cur.execute("""
                INSERT INTO menu (id, name, price)
                VALUES (%s, %s, %s)
            """, (
                int(item["id"]),
                str(item["name"]),
                int(item["price"])
            ))

        cur.execute("DELETE FROM orders")

        for order in data.get("orders", []):
            cur.execute("""
                INSERT INTO orders (id, data)
                VALUES (%s, %s)
            """, (
                int(order["id"]),
                json.dumps(order, ensure_ascii=False)
            ))

        conn.commit()
        cur.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
