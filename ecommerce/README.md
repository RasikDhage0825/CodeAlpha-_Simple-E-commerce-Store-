# Shopwell — Basic E-commerce Site

A working e-commerce demo: product listings, product detail pages, a shopping
cart, user registration/login, and order processing, backed by SQLite.

> **Note on stack:** you asked for Django or Express — this build uses
> **Flask (Python) + SQLite** instead, because the environment this was built
> in has no internet access to `pip install django` or `npm install express`.
> Flask is a close cousin of Django (same language, same request/response
> model, same templating heritage) and this was actually run and tested here.
> The architecture (REST API + static HTML/CSS/JS frontend, SQL schema, and
> route design) maps directly onto Django or Express if you'd rather port it —
> see "Porting" below.

## Features

- **Product listings** — grid view with live search and category filter
- **Product detail page** — full description, stock, quantity picker
- **Shopping cart** — add/update/remove items, persists per logged-in user
- **User registration/login** — hashed passwords (werkzeug), session cookies
- **Order processing** — checkout creates an order, decrements stock, clears cart
- **Order history** — past orders with line items and totals
- **Database** — SQLite file (`store.db`), auto-created and seeded with 12 sample products on first run

## Project structure

```
ecommerce/
├── app.py              # Flask app + all REST API routes
├── database.py          # SQLite schema, connection helper, seed data
├── requirements.txt
├── static/               # Frontend (HTML/CSS/vanilla JS), served by Flask
│   ├── index.html        # Product listing
│   ├── product.html      # Product detail
│   ├── cart.html         # Shopping cart / checkout
│   ├── login.html
│   ├── register.html
│   ├── orders.html        # Order history
│   ├── css/style.css
│   └── js/
│       ├── api.js         # fetch() wrapper + shared header logic
│       ├── main.js        # product grid + search/filter
│       ├── product.js     # product detail + add to cart
│       ├── cart.js        # cart page + checkout
│       ├── auth.js        # login/register forms
│       └── orders.js      # order history page
```

## Run it

```bash
cd ecommerce
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
python3 app.py
```

Open **http://localhost:5050** in your browser. The database is created and
seeded automatically on first run (`store.db`, SQLite — no separate DB server
needed). Delete `store.db` any time to reset to the seed data.

## Data model

- `users` — id, name, email (unique), password_hash, created_at
- `products` — id, name, description, price, image_url, category, stock, created_at
- `cart_items` — id, user_id, product_id, quantity (unique per user+product)
- `orders` — id, user_id, total, status, shipping_address, created_at
- `order_items` — id, order_id, product_id, product_name, price, quantity (price/name snapshotted at purchase time)

## API summary

| Method | Path                  | Auth | Description                        |
|--------|------------------------|------|-------------------------------------|
| POST   | /api/auth/register      | -    | Create account, starts session       |
| POST   | /api/auth/login         | -    | Log in, starts session               |
| POST   | /api/auth/logout        | ✓    | Clear session                        |
| GET    | /api/auth/me            | -    | Current user or `{user: null}`       |
| GET    | /api/products            | -    | List products (`?search=&category=`)|
| GET    | /api/products/:id        | -    | Product detail                       |
| GET    | /api/cart                | ✓    | Current user's cart + total          |
| POST   | /api/cart                 | ✓    | Add item `{product_id, quantity}`    |
| PUT    | /api/cart/:id             | ✓    | Update quantity (0 removes item)     |
| DELETE | /api/cart/:id             | ✓    | Remove item                          |
| POST   | /api/orders               | ✓    | Checkout `{shipping_address}`        |
| GET    | /api/orders               | ✓    | Order history                        |
| GET    | /api/orders/:id           | ✓    | Single order detail                  |

## Notes / production caveats

- `app.secret_key` is a hardcoded dev value — set the `SECRET_KEY` env var in production.
- Runs on Flask's dev server (`debug=True`) — use gunicorn/uwsgi behind nginx for production.
- Passwords are hashed with werkzeug's `generate_password_hash` (PBKDF2) — fine for a demo, `bcrypt`/`argon2` are stronger choices for production.
- No payment gateway integration — checkout just records the order and adjusts stock.

## Porting to Django or Express

The schema and route design translate directly:

- **Django**: each table → a model in `models.py`; each route → a DRF viewset
  or function-based view; `django.contrib.auth` replaces the hand-rolled
  session auth; templates or the same static frontend can stay as-is since it
  only talks to the API over `fetch()`.
- **Express**: each route → an Express router file; `better-sqlite3` or
  `pg`/Sequelize for the DB layer; `express-session` + `bcrypt` for auth. The
  static frontend can be served as-is from `express.static()`.
