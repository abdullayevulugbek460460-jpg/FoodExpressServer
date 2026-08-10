from flask import Flask, jsonify, request, send_from_directory
import os
from flask_cors import CORS
from database import load_data, save_data
from config import PORT

app = Flask(__name__)
CORS(app)

UPDATE_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "updates"
)


# =====================================================
# UPDATE
# =====================================================

@app.route("/update/version", methods=["GET"])
def update_version():
    version_file = os.path.join(
        UPDATE_FOLDER,
        "version.json"
    )

    if not os.path.exists(version_file):
        return jsonify({
            "success": False,
            "message": "Update ma'lumoti topilmadi"
        }), 404

    return send_from_directory(
        UPDATE_FOLDER,
        "version.json"
    )


@app.route("/updates/<path:filename>", methods=["GET"])
def download_update(filename):
    return send_from_directory(
        UPDATE_FOLDER,
        filename,
        as_attachment=True
    )


@app.route("/")
def home():
    return jsonify({
        "status": "FastFood Server ishlayapti"
    })


# =====================================================
# MENU
# =====================================================

@app.route("/menu", methods=["GET"])
def menu():
    data = load_data()

    return jsonify({
        "menu": data.get("menu", [])
    })


@app.route("/menu", methods=["POST"])
def add_menu_item():
    data = load_data()
    req = request.get_json(silent=True) or {}

    name = str(req.get("name", "")).strip()
    price = req.get("price")

    if not name:
        return jsonify({
            "success": False,
            "message": "Mahsulot nomi kerak"
        }), 400

    try:
        price = int(price)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "Narx noto'g'ri"
        }), 400

    if price < 0:
        return jsonify({
            "success": False,
            "message": "Narx 0 dan kichik bo'lishi mumkin emas"
        }), 400

    menu = data.setdefault("menu", [])

    new_id = max(
        [int(item.get("id", 0)) for item in menu] or [0]
    ) + 1

    item = {
        "id": new_id,
        "name": name,
        "price": price
    }

    menu.append(item)
    save_data(data)

    return jsonify({
        "success": True,
        "message": "Mahsulot qo'shildi",
        "item": item
    }), 201


@app.route("/menu/<int:item_id>", methods=["PUT"])
def update_menu_item(item_id):
    data = load_data()
    req = request.get_json(silent=True) or {}

    for item in data.get("menu", []):

        if item.get("id") == item_id:

            if "name" in req:
                name = str(req.get("name", "")).strip()

                if not name:
                    return jsonify({
                        "success": False,
                        "message": "Mahsulot nomi bo'sh bo'lishi mumkin emas"
                    }), 400

                item["name"] = name

            if "price" in req:
                try:
                    price = int(req.get("price"))
                except (TypeError, ValueError):
                    return jsonify({
                        "success": False,
                        "message": "Narx noto'g'ri"
                    }), 400

                if price < 0:
                    return jsonify({
                        "success": False,
                        "message": "Narx 0 dan kichik bo'lishi mumkin emas"
                    }), 400

                item["price"] = price

            save_data(data)

            return jsonify({
                "success": True,
                "message": "Mahsulot yangilandi",
                "item": item
            })

    return jsonify({
        "success": False,
        "message": "Mahsulot topilmadi"
    }), 404


@app.route("/menu/<int:item_id>", methods=["DELETE"])
def delete_menu_item(item_id):
    data = load_data()
    menu = data.get("menu", [])

    for item in menu:

        if item.get("id") == item_id:
            menu.remove(item)
            data["menu"] = menu
            save_data(data)

            return jsonify({
                "success": True,
                "message": "Mahsulot o'chirildi"
            })

    return jsonify({
        "success": False,
        "message": "Mahsulot topilmadi"
    }), 404


# =====================================================
# COURIERS
# =====================================================

@app.route("/courier/register", methods=["POST"])
def courier_register():

    data = load_data()

    req = request.get_json(silent=True) or {}

    name = str(req.get("name", "")).strip()
    phone = str(req.get("phone", "")).strip()

    if not name:
        return jsonify({
            "success": False,
            "message": "Kuryer ismi kerak"
        }), 400

    if not phone:
        return jsonify({
            "success": False,
            "message": "Telefon raqam kerak"
        }), 400

    couriers = data.setdefault("couriers", [])

    for courier in couriers:

        if courier.get("phone") == phone:

            return jsonify({
                "success": True,
                "message": "Kuryer mavjud",
                "courier": courier
            })

    new_id = max(
        [int(c.get("id", 0)) for c in couriers] or [0]
    ) + 1

    courier = {
        "id": new_id,
        "name": name,
        "phone": phone,
        "online": False,
        "balance": 0,
        "completed_orders": 0
    }

    couriers.append(courier)

    save_data(data)

    return jsonify({
        "success": True,
        "message": "Kuryer ro'yxatdan o'tdi",
        "courier": courier
    }), 201


@app.route("/courier/<int:courier_id>/online", methods=["POST"])
def courier_online(courier_id):

    data = load_data()

    req = request.get_json(silent=True) or {}

    online = bool(req.get("online", False))

    for courier in data.get("couriers", []):

        if courier.get("id") == courier_id:

            courier["online"] = online

            save_data(data)

            return jsonify({
                "success": True,
                "message": "Online holat yangilandi",
                "courier": courier
            })

    return jsonify({
        "success": False,
        "message": "Kuryer topilmadi"
    }), 404


@app.route("/couriers", methods=["GET"])
def couriers():

    data = load_data()

    return jsonify({
        "couriers": data.get("couriers", [])
    })


# =====================================================
# CREATE ORDER
# =====================================================

@app.route("/order", methods=["POST"])
def create_order():

    data = load_data()

    order = request.get_json(silent=True) or {}

    orders = data.setdefault("orders", [])

    new_id = max(
        [int(o.get("id", 0)) for o in orders] or [0]
    ) + 1

    order["id"] = new_id
    order["status"] = "Yangi"
    order["courier_id"] = None

    orders.append(order)

    save_data(data)

    return jsonify({
        "success": True,
        "message": "Buyurtma qabul qilindi",
        "order": order
    })


# =====================================================
# ORDERS
# =====================================================

@app.route("/orders", methods=["GET"])
def orders():

    data = load_data()

    courier_id = request.args.get("courier_id")

    result = []

    for order in data.get("orders", []):

        # Yetkazilgan buyurtmalarni ham qaytaramiz
        # Admin uchun kerak bo'ladi.
        if courier_id is not None:

            try:
                cid = int(courier_id)
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "courier_id noto'g'ri"
                }), 400

            # Yangi buyurtma barcha kuryerlarga ko'rinadi.
            # Biriktirilgan buyurtma esa faqat o'z kuryeriga.
            if order.get("status") == "Yangi":
                result.append(order)

            elif order.get("courier_id") == cid:
                result.append(order)

        else:
            result.append(order)

    return jsonify({
        "orders": result
    })


# =====================================================
# ACCEPT ORDER
# =====================================================

@app.route("/order/<int:order_id>/accept", methods=["POST"])
def accept_order(order_id):

    data = load_data()

    req = request.get_json(silent=True) or {}

    courier_id = req.get("courier_id")

    try:
        courier_id = int(courier_id)
    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "courier_id kerak"
        }), 400

    courier = None

    for c in data.get("couriers", []):

        if c.get("id") == courier_id:
            courier = c
            break

    if courier is None:
        return jsonify({
            "success": False,
            "message": "Kuryer topilmadi"
        }), 404

    if not courier.get("online", False):
        return jsonify({
            "success": False,
            "message": "Kuryer offline"
        }), 400

    for order in data.get("orders", []):

        if order.get("id") == order_id:

            # Eng muhim himoya:
            # Zakazni birinchi olgan kuryer yutadi.
            if order.get("courier_id") is not None:

                return jsonify({
                    "success": False,
                    "message": "Bu buyurtma allaqachon boshqa kuryer tomonidan olindi",
                    "order": order
                }), 409

            if order.get("status") != "Yangi":

                return jsonify({
                    "success": False,
                    "message": "Bu buyurtma endi mavjud emas",
                    "order": order
                }), 409

            order["courier_id"] = courier_id
            order["status"] = "Yo‘lda"

            save_data(data)

            return jsonify({
                "success": True,
                "message": "Buyurtma sizga biriktirildi",
                "order": order
            })

    return jsonify({
        "success": False,
        "message": "Buyurtma topilmadi"
    }), 404


# =====================================================
# UPDATE ORDER STATUS
# =====================================================

@app.route("/order/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id):

    data = load_data()

    req = request.get_json(silent=True) or {}

    new_status = str(
        req.get("status", "")
    ).strip()

    courier_id = req.get("courier_id")

    if new_status == "Yo'lda":
        new_status = "Yo‘lda"

    allowed_statuses = [
        "Yangi",
        "Tayyorlanmoqda",
        "Yo‘lda",
        "Yetkazildi",
        "Bekor qilindi"
    ]

    if new_status not in allowed_statuses:

        return jsonify({
            "success": False,
            "message": "Noto'g'ri status"
        }), 400

    for order in data.get("orders", []):

        if order.get("id") == order_id:

            # Kuryer statusini o'zgartirayotgan bo'lsa
            if courier_id is not None:

                try:
                    courier_id = int(courier_id)
                except ValueError:

                    return jsonify({
                        "success": False,
                        "message": "courier_id noto'g'ri"
                    }), 400

                if order.get("courier_id") != courier_id:

                    return jsonify({
                        "success": False,
                        "message": "Bu buyurtma sizga biriktirilmagan"
                    }), 403

            # Yangi zakazni Yo'lda qilish
            # faqat accept endpoint orqali.
            if new_status == "Yo‘lda":
                if order.get("courier_id") is None:

                    return jsonify({
                        "success": False,
                        "message": "Avval buyurtmani qabul qiling"
                    }), 409

            order["status"] = new_status

            # Yetkazilganda kuryer statistikasini oshiramiz
            if new_status == "Yetkazildi":

                cid = order.get("courier_id")

                for courier in data.get("couriers", []):

                    if courier.get("id") == cid:

                        courier["completed_orders"] = (
                            int(
                                courier.get(
                                    "completed_orders",
                                    0
                                )
                            ) + 1
                        )

                        try:
                            total = int(
                                order.get("total", 0)
                            )
                        except (TypeError, ValueError):
                            total = 0

                        courier["balance"] = (
                            int(
                                courier.get(
                                    "balance",
                                    0
                                )
                            ) + total
                        )

                        break

            save_data(data)

            return jsonify({
                "success": True,
                "message": "Status yangilandi",
                "order": order
            })

    return jsonify({
        "success": False,
        "message": "Buyurtma topilmadi"
    }), 404


# =====================================================
# CLIENT UPDATE
# =====================================================

@app.route("/update/client/version", methods=["GET"])
def client_update_version():

    return jsonify({
        "versionCode": 2,
        "versionName": "1.0.1",
        "apk": "/updates/client/FoodExpress.apk",
        "message": "FoodExpress yangi versiyasi mavjud!"
    })


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    print("FastFood Server ishga tushdi...")

    app.run(
        host="0.0.0.0",
        port=PORT
    )
