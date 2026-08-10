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

def get_courier_commission():
    """Admin panel uchun kuryer komissiya foizini olish."""
    if not DATABASE_URL:
        return 10

    init_db()
    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        cur.execute("""
            INSERT INTO app_settings (key, value)
            VALUES ('courier_commission', '10')
            ON CONFLICT (key) DO NOTHING
        """)

        cur.execute("""
            SELECT value
            FROM app_settings
            WHERE key = 'courier_commission'
        """)

        row = cur.fetchone()
        conn.commit()

        try:
            return max(0, min(100, int(row[0]))) if row else 10
        except (TypeError, ValueError):
            return 10

    finally:
        conn.close()


def set_courier_commission(percent):
    """Admin panel kiritgan kuryer komissiya foizini saqlash."""
    percent = int(percent)

    if percent < 0 or percent > 100:
        raise ValueError("Foiz 0 dan 100 gacha bo'lishi kerak")

    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL mavjud emas")

    init_db()
    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)

        cur.execute("""
            INSERT INTO app_settings (key, value)
            VALUES ('courier_commission', %s)
            ON CONFLICT (key)
            DO UPDATE SET value = EXCLUDED.value
        """, (str(percent),))

        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


def accept_order_atomic(order_id, courier_id):
    """
    Buyurtmani faqat birinchi kuryerga atomik tarzda biriktiradi.
    Ikkinchi kuryer bir vaqtning o'zida urinsa, buyurtma allaqachon olingan bo'ladi.
    """

    if not DATABASE_URL:
        return {
            "success": False,
            "message": "DATABASE_URL mavjud emas"
        }

    init_db()

    conn = get_connection()

    try:
        cur = conn.cursor()

        # Kuryer online ekanini tekshirish
        cur.execute("""
            SELECT id, name, phone, online, balance, completed_orders
            FROM couriers
            WHERE id = %s
        """, (courier_id,))

        courier_row = cur.fetchone()

        if courier_row is None:
            conn.rollback()
            return {
                "success": False,
                "message": "Kuryer topilmadi"
            }

        if not courier_row[3]:
            conn.rollback()
            return {
                "success": False,
                "message": "Kuryer offline"
            }

        # Eng muhim qism:
        # Faqat Yangi va courier_id NULL bo'lgan buyurtmani o'zgartiramiz.
        cur.execute("""
            UPDATE orders
            SET data = jsonb_set(
                jsonb_set(
                    data,
                    '{courier_id}',
                    to_jsonb(%s::integer)
                ),
                '{status}',
                '"Yo‘lda"'::jsonb
            )
            WHERE id = %s
              AND data->>'status' = 'Yangi'
              AND data->>'courier_id' IS NULL
            RETURNING data
        """, (
            courier_id,
            order_id
        ))

        row = cur.fetchone()

        if row is None:
            conn.rollback()

            # Buyurtma mavjudligini tekshiramiz
            cur.execute("""
                SELECT data
                FROM orders
                WHERE id = %s
            """, (order_id,))

            existing = cur.fetchone()

            if existing is None:
                return {
                    "success": False,
                    "message": "Buyurtma topilmadi"
                }

            return {
                "success": False,
                "message": "Bu buyurtma allaqachon boshqa kuryer tomonidan olindi",
                "order": existing[0]
            }

        conn.commit()

        return {
            "success": True,
            "message": "Buyurtma sizga biriktirildi",
            "order": row[0]
        }

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()
