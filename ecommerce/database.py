"""
Database layer for the e-commerce app.
Uses Python's built-in sqlite3 module - no external DB server required.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "store.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL,
    image_url TEXT NOT NULL,
    category TEXT NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cart_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    UNIQUE(user_id, product_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    total REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    shipping_address TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    product_name TEXT NOT NULL,
    price REAL NOT NULL,
    quantity INTEGER NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
"""

SEED_PRODUCTS = [
    ("Wireless Headphones", "Over-ear Bluetooth headphones with active noise cancellation and 30-hour battery life.", 79.99, "https://picsum.photos/seed/headphones/400/400", "Electronics", 25),
    ("Mechanical Keyboard", "Compact 65% mechanical keyboard with hot-swappable switches and RGB backlighting.", 64.50, "https://picsum.photos/seed/keyboard/400/400", "Electronics", 40),
    ("Running Shoes", "Lightweight running shoes with breathable mesh and responsive cushioning.", 89.00, "https://picsum.photos/seed/shoes/400/400", "Sportswear", 60),
    ("Ceramic Coffee Mug", "12oz hand-glazed ceramic mug, microwave and dishwasher safe.", 14.99, "https://picsum.photos/seed/mug/400/400", "Home", 100),
    ("Yoga Mat", "Non-slip 6mm yoga mat with carrying strap, eco-friendly TPE material.", 29.95, "https://picsum.photos/seed/yoga/400/400", "Sportswear", 45),
    ("Stainless Water Bottle", "Insulated 750ml water bottle, keeps drinks cold for 24 hours.", 24.00, "https://picsum.photos/seed/bottle/400/400", "Home", 80),
    ("Leather Wallet", "Slim bifold wallet made from genuine full-grain leather.", 39.99, "https://picsum.photos/seed/wallet/400/400", "Accessories", 35),
    ("Backpack", "Water-resistant 25L backpack with padded laptop sleeve.", 54.99, "https://picsum.photos/seed/backpack/400/400", "Accessories", 30),
    ("Desk Lamp", "LED desk lamp with adjustable brightness and USB charging port.", 32.50, "https://picsum.photos/seed/lamp/400/400", "Home", 50),
    ("Bluetooth Speaker", "Portable waterproof speaker with 12-hour playtime and deep bass.", 45.00, "https://picsum.photos/seed/speaker/400/400", "Electronics", 55),
    ("Sunglasses", "Polarized UV400 sunglasses with a classic frame.", 19.99, "https://picsum.photos/seed/sunglasses/400/400", "Accessories", 70),
    ("Notebook Set", "Set of 3 dotted notebooks with 120 pages each, hardcover.", 16.75, "https://picsum.photos/seed/notebook/400/400", "Stationery", 90),
]


def get_db():
    """Return a connection with row access by column name and FK enforcement on."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(seed=True):
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()

    if seed:
        count = conn.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        if count == 0:
            now = datetime.utcnow().isoformat()
            conn.executemany(
                """INSERT INTO products (name, description, price, image_url, category, stock, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                [(*p, now) for p in SEED_PRODUCTS],
            )
            conn.commit()
    conn.close()


if __name__ == "__main__":
    # Allow running `python database.py` to (re)initialize the DB.
    init_db()
    print(f"Database initialized at {DB_PATH}")
