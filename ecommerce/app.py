"""
E-commerce backend - Flask + SQLite.

REST API consumed by the static HTML/CSS/JS frontend in /static.
Session-based auth (signed cookies) using werkzeug's password hashing.
"""
from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os

from database import get_db, init_db

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return wrapper


def current_user_row(conn):
    return conn.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?",
        (session["user_id"],),
    ).fetchone()


def row_to_dict(row):
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------
@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------
@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "An account with that email already exists"}), 409

    password_hash = generate_password_hash(password)
    now = datetime.utcnow().isoformat()
    cur = conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        (name, email, password_hash, now),
    )
    conn.commit()
    user_id = cur.lastrowid
    conn.close()

    session["user_id"] = user_id
    return jsonify({"id": user_id, "name": name, "email": email}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    return jsonify({"id": user["id"], "name": user["name"], "email": user["email"]})


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@app.route("/api/auth/me", methods=["GET"])
def me():
    if "user_id" not in session:
        return jsonify({"user": None})
    conn = get_db()
    user = current_user_row(conn)
    conn.close()
    return jsonify({"user": row_to_dict(user)})


# ---------------------------------------------------------------------------
# Product routes
# ---------------------------------------------------------------------------
@app.route("/api/products", methods=["GET"])
def list_products():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()

    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        like = f"%{search}%"
        params += [like, like]
    if category:
        query += " AND category = ?"
        params.append(category)
    query += " ORDER BY created_at DESC"

    conn = get_db()
    products = [dict(r) for r in conn.execute(query, params).fetchall()]
    categories = [r["category"] for r in conn.execute("SELECT DISTINCT category FROM products").fetchall()]
    conn.close()
    return jsonify({"products": products, "categories": categories})


@app.route("/api/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify(dict(product))


# ---------------------------------------------------------------------------
# Cart routes (per logged-in user)
# ---------------------------------------------------------------------------
@app.route("/api/cart", methods=["GET"])
@login_required
def get_cart():
    conn = get_db()
    rows = conn.execute(
        """SELECT ci.id AS cart_item_id, ci.quantity, p.id AS product_id, p.name,
                  p.price, p.image_url, p.stock
           FROM cart_items ci JOIN products p ON p.id = ci.product_id
           WHERE ci.user_id = ?
           ORDER BY ci.id""",
        (session["user_id"],),
    ).fetchall()
    conn.close()
    items = [dict(r) for r in rows]
    total = round(sum(i["price"] * i["quantity"] for i in items), 2)
    return jsonify({"items": items, "total": total})


@app.route("/api/cart", methods=["POST"])
@login_required
def add_to_cart():
    data = request.get_json(silent=True) or {}
    product_id = data.get("product_id")
    quantity = int(data.get("quantity", 1))

    if not product_id or quantity < 1:
        return jsonify({"error": "product_id and a positive quantity are required"}), 400

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({"error": "Product not found"}), 404

    existing = conn.execute(
        "SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?",
        (session["user_id"], product_id),
    ).fetchone()

    new_qty = quantity + (existing["quantity"] if existing else 0)
    if new_qty > product["stock"]:
        conn.close()
        return jsonify({"error": f"Only {product['stock']} in stock"}), 400

    if existing:
        conn.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (new_qty, existing["id"]))
    else:
        conn.execute(
            "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
            (session["user_id"], product_id, quantity),
        )
    conn.commit()
    conn.close()
    return jsonify({"message": "Added to cart"}), 201


@app.route("/api/cart/<int:cart_item_id>", methods=["PUT"])
@login_required
def update_cart_item(cart_item_id):
    data = request.get_json(silent=True) or {}
    quantity = int(data.get("quantity", 1))

    conn = get_db()
    item = conn.execute(
        "SELECT * FROM cart_items WHERE id = ? AND user_id = ?",
        (cart_item_id, session["user_id"]),
    ).fetchone()
    if not item:
        conn.close()
        return jsonify({"error": "Cart item not found"}), 404

    if quantity < 1:
        conn.execute("DELETE FROM cart_items WHERE id = ?", (cart_item_id,))
    else:
        product = conn.execute("SELECT stock FROM products WHERE id = ?", (item["product_id"],)).fetchone()
        if quantity > product["stock"]:
            conn.close()
            return jsonify({"error": f"Only {product['stock']} in stock"}), 400
        conn.execute("UPDATE cart_items SET quantity = ? WHERE id = ?", (quantity, cart_item_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Cart updated"})


@app.route("/api/cart/<int:cart_item_id>", methods=["DELETE"])
@login_required
def remove_cart_item(cart_item_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM cart_items WHERE id = ? AND user_id = ?",
        (cart_item_id, session["user_id"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Item removed"})


# ---------------------------------------------------------------------------
# Order routes
# ---------------------------------------------------------------------------
@app.route("/api/orders", methods=["POST"])
@login_required
def create_order():
    data = request.get_json(silent=True) or {}
    shipping_address = (data.get("shipping_address") or "").strip()
    if not shipping_address:
        return jsonify({"error": "Shipping address is required"}), 400

    conn = get_db()
    cart_rows = conn.execute(
        """SELECT ci.id AS cart_item_id, ci.quantity, p.id AS product_id, p.name,
                  p.price, p.stock
           FROM cart_items ci JOIN products p ON p.id = ci.product_id
           WHERE ci.user_id = ?""",
        (session["user_id"],),
    ).fetchall()

    if not cart_rows:
        conn.close()
        return jsonify({"error": "Your cart is empty"}), 400

    # Validate stock before committing anything
    for item in cart_rows:
        if item["quantity"] > item["stock"]:
            conn.close()
            return jsonify({"error": f"Not enough stock for {item['name']}"}), 400

    total = round(sum(i["price"] * i["quantity"] for i in cart_rows), 2)
    now = datetime.utcnow().isoformat()

    try:
        cur = conn.execute(
            """INSERT INTO orders (user_id, total, status, shipping_address, created_at)
               VALUES (?, ?, 'processing', ?, ?)""",
            (session["user_id"], total, shipping_address, now),
        )
        order_id = cur.lastrowid

        for item in cart_rows:
            conn.execute(
                """INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                   VALUES (?, ?, ?, ?, ?)""",
                (order_id, item["product_id"], item["name"], item["price"], item["quantity"]),
            )
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )

        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (session["user_id"],))
        conn.commit()
    except Exception as exc:  # rollback on any failure so we never lose stock/order consistency
        conn.rollback()
        conn.close()
        return jsonify({"error": f"Order failed: {exc}"}), 500

    conn.close()
    return jsonify({"message": "Order placed", "order_id": order_id, "total": total}), 201


@app.route("/api/orders", methods=["GET"])
@login_required
def list_orders():
    conn = get_db()
    orders = conn.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (session["user_id"],),
    ).fetchall()
    result = []
    for order in orders:
        items = conn.execute(
            "SELECT * FROM order_items WHERE order_id = ?", (order["id"],)
        ).fetchall()
        d = dict(order)
        d["items"] = [dict(i) for i in items]
        result.append(d)
    conn.close()
    return jsonify({"orders": result})


@app.route("/api/orders/<int:order_id>", methods=["GET"])
@login_required
def get_order(order_id):
    conn = get_db()
    order = conn.execute(
        "SELECT * FROM orders WHERE id = ? AND user_id = ?",
        (order_id, session["user_id"]),
    ).fetchone()
    if not order:
        conn.close()
        return jsonify({"error": "Order not found"}), 404
    items = conn.execute("SELECT * FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
    conn.close()
    d = dict(order)
    d["items"] = [dict(i) for i in items]
    return jsonify(d)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5050, debug=True)
