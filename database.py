import os
import json
from config import DATA_FILE

DATABASE_URL = os.environ.get("DATABASE_URL")


def load_json_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "menu": [],
            "orders": [],
            "couriers": []
        }


def save_json_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def get_connection():
    import psycopg2
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()

    try:
        cur = conn.cursor()

        # MENU
        cur.execute("""
            CREATE TABLE IF NOT EXISTS menu (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price INTEGER NOT NULL
            )
        """)

        # ORDERS
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id BIGINT PRIMARY KEY,
                data JSONB NOT NULL
            )
        """)

        # COURIERS
        cur.execute("""
            CREATE TABLE IF NOT EXISTS couriers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                online BOOLEAN NOT NULL DEFAULT FALSE,
                balance BIGINT NOT NULL DEFAULT 0,
                completed_orders INTEGER NOT NULL DEFAULT 0
            )
        """)

        conn.commit()
        cur.close()

    finally:
        conn.close()


def import_json_if_empty():
    """
    PostgreSQL bo'sh bo'lsa eski data.json
    ma'lumotlarini bir marta import qiladi.
    """

    local_data = load_json_data()

    conn = get_connection()

    try:
        cur = conn.cursor()

        # =========================
        # MENU
        # =========================

        cur.execute("SELECT COUNT(*) FROM menu")
        menu_count = cur.fetchone()[0]

        if menu_count == 0:

            for item in local_data.get("menu", []):

                try:
                    cur.execute("""
                        INSERT INTO menu (
                            id,
                            name,
                            price
                        )
                        VALUES (%s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        int(item["id"]),
                        str(item["name"]),
                        int(item["price"])
                    ))

                except Exception:
                    pass

        # =========================
        # ORDERS
        # =========================

        cur.execute("SELECT COUNT(*) FROM orders")
        orders_count = cur.fetchone()[0]

        if orders_count == 0:

            for order in local_data.get("orders", []):

                try:
                    cur.execute("""
                        INSERT INTO orders (
                            id,
                            data
                        )
                        VALUES (%s, %s)
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        int(order["id"]),
                        json.dumps(
                            order,
                            ensure_ascii=False
                        )
                    ))

                except Exception:
                    pass

        # =========================
        # COURIERS
        # =========================

        cur.execute("SELECT COUNT(*) FROM couriers")
        couriers_count = cur.fetchone()[0]

        if couriers_count == 0:

            for courier in local_data.get("couriers", []):

                try:
                    cur.execute("""
                        INSERT INTO couriers (
                            id,
                            name,
                            phone,
                            online,
                            balance,
                            completed_orders
                        )
                        VALUES (
                            %s,
                            %s,
                            %s,
                            %s,
                            %s,
                            %s
                        )
                        ON CONFLICT (id) DO NOTHING
                    """, (
                        int(courier["id"]),
                        str(courier["name"]),
                        str(courier["phone"]),
                        bool(courier.get("online", False)),
                        int(courier.get("balance", 0)),
                        int(
                            courier.get(
                                "completed_orders",
                                0
                            )
                        )
                    ))

                except Exception:
                    pass

        conn.commit()
        cur.close()

    finally:
        conn.close()


def load_data():

    # DATABASE_URL bo'lmasa eski JSON rejimi
    if not DATABASE_URL:
        return load_json_data()

    init_db()

    # Birinchi ishga tushishda eski ma'lumotlarni import qilish
    import_json_if_empty()

    conn = get_connection()

    try:
        cur = conn.cursor()

        # =========================
        # MENU
        # =========================

        cur.execute("""
            SELECT
                id,
                name,
                price
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

        # =========================
        # ORDERS
        # =========================

        cur.execute("""
            SELECT data
            FROM orders
            ORDER BY id
        """)

        orders = [
            row[0]
            for row in cur.fetchall()
        ]

        # =========================
        # COURIERS
        # =========================

        cur.execute("""
            SELECT
                id,
                name,
                phone,
                online,
                balance,
                completed_orders
            FROM couriers
            ORDER BY id
        """)

        couriers = [
            {
                "id": row[0],
                "name": row[1],
                "phone": row[2],
                "online": row[3],
                "balance": row[4],
                "completed_orders": row[5]
            }
            for row in cur.fetchall()
        ]

        cur.close()

        return {
            "menu": menu,
            "orders": orders,
            "couriers": couriers
        }

    finally:
        conn.close()


def save_data(data):

    # DATABASE_URL bo'lmasa JSON
    if not DATABASE_URL:
        save_json_data(data)
        return

    init_db()

    conn = get_connection()

    try:
        cur = conn.cursor()

        # =========================
        # MENU
        # =========================

        cur.execute("DELETE FROM menu")

        for item in data.get("menu", []):

            cur.execute("""
                INSERT INTO menu (
                    id,
                    name,
                    price
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    price = EXCLUDED.price
            """, (
                int(item["id"]),
                str(item["name"]),
                int(item["price"])
            ))

        # =========================
        # ORDERS
        # =========================

        cur.execute("DELETE FROM orders")

        for order in data.get("orders", []):

            cur.execute("""
                INSERT INTO orders (
                    id,
                    data
                )
                VALUES (%s, %s)
                ON CONFLICT (id)
                DO UPDATE SET
                    data = EXCLUDED.data
            """, (
                int(order["id"]),
                json.dumps(
                    order,
                    ensure_ascii=False
                )
            ))

        # =========================
        # COURIERS
        # =========================

        cur.execute("DELETE FROM couriers")

        for courier in data.get("couriers", []):

            cur.execute("""
                INSERT INTO couriers (
                    id,
                    name,
                    phone,
                    online,
                    balance,
                    completed_orders
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                ON CONFLICT (id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    phone = EXCLUDED.phone,
                    online = EXCLUDED.online,
                    balance = EXCLUDED.balance,
                    completed_orders =
                        EXCLUDED.completed_orders
            """, (
                int(courier["id"]),
                str(courier["name"]),
                str(courier["phone"]),
                bool(courier.get("online", False)),
                int(courier.get("balance", 0)),
                int(
                    courier.get(
                        "completed_orders",
                        0
                    )
                )
            ))

        conn.commit()
        cur.close()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
