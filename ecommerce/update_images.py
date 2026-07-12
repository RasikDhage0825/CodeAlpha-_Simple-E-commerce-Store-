"""
One-off script to swap the placeholder product images for specific, real
stock photos that actually match each product (hosted on Pexels' CDN, which
explicitly allows free hotlinking/use - see pexels.com/license).

Run this from inside the ecommerce folder:
    python update_images.py
"""
import sqlite3
from database import DB_PATH

# Each entry is a Pexels photo ID for a photo that actually matches the
# product. Pexels serves images at a predictable CDN URL built from the ID.
# Want a different look for any product? Find a photo on pexels.com, grab
# the number at the end of its URL (e.g. .../photo/some-title-1234567/),
# and drop it in below.
IMAGE_IDS = {
    "Wireless Headphones": 610945,       # black headphones on a table
    "Mechanical Keyboard": 14267038,     # compact mechanical keyboard
    "Running Shoes": 8373048,            # grey running sneakers
    "Ceramic Coffee Mug": 606542,        # white ceramic mug
    "Yoga Mat": 7318664,                 # rolled yoga mats
    "Stainless Water Bottle": 9160531,   # steel tumbler/bottle
    "Leather Wallet": 915917,            # brown leather wallet
    "Backpack": 3731256,                 # black backpack, white background
    "Desk Lamp": 7193653,                # minimalist adjustable desk lamp
    "Bluetooth Speaker": 18542239,       # portable wireless speaker
    "Sunglasses": 31305965,              # black sunglasses, product shot
    "Notebook Set": 7054755,             # stack of notebooks
}

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

updated = 0
for name, photo_id in IMAGE_IDS.items():
    url = f"https://images.pexels.com/photos/{photo_id}/pexels-photo-{photo_id}.jpeg?auto=compress&cs=tinysrgb&w=600"
    result = cur.execute(
        "UPDATE products SET image_url = ? WHERE name = ?", (url, name)
    )
    if result.rowcount:
        updated += result.rowcount
        print(f"Updated '{name}' -> {url}")
    else:
        print(f"No product found named '{name}' (skipped)")

conn.commit()
conn.close()
print(f"\nDone. {updated} product(s) updated.")
