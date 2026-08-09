from flask import Flask, jsonify, request, send_from_directory
import os
from flask_cors import CORS

from database import load_data, save_data
from config import PORT


app = Flask(__name__)

UPDATE_FOLDER = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "updates"
)


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


CORS(app)


@app.route("/")
def home():
    return jsonify({
        "status": "FastFood Server ishlayapti"
    })


# Menyu olish
@app.route("/menu", methods=["GET"])
def menu():
    data = load_data()

    return jsonify({
        "menu": data["menu"]
    })


# =====================================================
# MENYU BOSHQARUVI
# =====================================================

# Yangi mahsulot qo'shish
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

    menu = data.get("menu", [])

    new_id = max(
        [int(item.get("id", 0)) for item in menu] or [0]
    ) + 1

    item = {
        "id": new_id,
        "name": name,
        "price": price
    }

    menu.append(item)
    data["menu"] = menu
    save_data(data)

    return jsonify({
        "success": True,
        "message": "Mahsulot qo'shildi",
        "item": item
    }), 201


# Mahsulotni o'zgartirish
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


# Mahsulotni o'chirish
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



# Buyurtma berish
@app.route("/order", methods=["POST"])
def create_order():

    data = load_data()

    order = request.json

    order["id"] = len(data["orders"]) + 1
    order["status"] = "Yangi"

    data["orders"].append(order)

    save_data(data)

    return jsonify({
        "success": True,
        "message": "Buyurtma qabul qilindi",
        "order": order
    })


# Buyurtma statusini o'zgartirish
@app.route("/order/<int:order_id>/status", methods=["POST"])
def update_order_status(order_id):

    data = load_data()
    req = request.get_json(silent=True) or {}

    new_status = req.get("status", "").strip()

    # Apostrof yozilishidagi farqni standartlashtirish
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

    for order in data["orders"]:
        if order.get("id") == order_id:
            order["status"] = new_status
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



# Mijoz APK versiyasini tekshirish
@app.route("/update/client/version", methods=["GET"])
def client_update_version():

    return jsonify({
        "versionCode": 2,
        "versionName": "1.0.1",
        "apk": "/updates/client/FoodExpress.apk",
        "message": "FoodExpress yangi versiyasi mavjud!"
    })



# Barcha buyurtmalar
@app.route("/orders", methods=["GET"])
def orders():

    data = load_data()

    return jsonify({
        "orders": data["orders"]
    })


if __name__ == "__main__":
    print("FastFood Server ishga tushdi...")
    app.run(
        host="0.0.0.0",
        port=PORT
    )
