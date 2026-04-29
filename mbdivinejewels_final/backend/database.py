import sqlite3, bcrypt, json
from pathlib import Path
from contextlib import contextmanager

import os as _os
_db_dir = _os.getenv("DB_DIR", str(Path(__file__).parent.parent / "data"))
DB_PATH = Path(_db_dir) / "mbdivine.db"

def _connect():
    db = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA foreign_keys=ON")
    return db

def get_db():
    db = _connect()
    try:
        yield db
    finally:
        db.close()

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = _connect()

    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            cat TEXT DEFAULT 'Other',
            mat TEXT DEFAULT 'Gold plate',
            size TEXT DEFAULT '',
            description TEXT DEFAULT '',
            photo TEXT,
            photos TEXT DEFAULT '[]',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            items TEXT NOT NULL,
            total REAL NOT NULL,
            pay TEXT NOT NULL,
            time TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS customer_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            customer_note TEXT DEFAULT '',
            items TEXT NOT NULL,
            total REAL NOT NULL,
            shipping_fee REAL DEFAULT 0,
            payment_method TEXT DEFAULT 'upi',
            payment_proof TEXT DEFAULT NULL,
            payment_txn_id TEXT DEFAULT '',
            time TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payment_settings (
            id INTEGER PRIMARY KEY CHECK (id=1),
            data TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS store_settings (
            id INTEGER PRIMARY KEY CHECK (id=1),
            data TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS story_section (
            id INTEGER PRIMARY KEY CHECK (id=1),
            data TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS testimonials_section (
            id INTEGER PRIMARY KEY CHECK (id=1),
            data TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS gallery_section (
            id INTEGER PRIMARY KEY CHECK (id=1),
            data TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            sort_order INTEGER DEFAULT 0
        );
    """)

    # ── Safe column migrations for existing DBs ──
    migrations = [
        ("products", "description", "TEXT DEFAULT ''"),
        ("products", "photos",      "TEXT DEFAULT '[]'"),
        ("customer_orders", "shipping_fee",   "REAL DEFAULT 0"),
        ("customer_orders", "payment_method", "TEXT DEFAULT 'upi'"),
        ("customer_orders", "payment_proof",  "TEXT DEFAULT NULL"),
        ("customer_orders", "payment_txn_id", "TEXT DEFAULT ''"),
    ]
    for table, col, defn in migrations:
        try:
            db.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
        except Exception:
            pass

    # ── Seed admin ──
    if not db.execute("SELECT id FROM users WHERE email=?", ("admin@mbdivine.com",)).fetchone():
        db.execute(
            "INSERT INTO users (email,password_hash) VALUES (?,?)",
            ("admin@mbdivine.com", bcrypt.hashpw("divine123".encode(), bcrypt.gensalt()).decode())
        )
        print("✅ Admin created: admin@mbdivine.com / divine123")

    # ── Seed payment settings ──
    if not db.execute("SELECT id FROM payment_settings WHERE id=1").fetchone():
        db.execute("INSERT INTO payment_settings (id,data) VALUES (1,?)", (json.dumps({
            "upi": "", "upiName": "", "bankName": "", "bankAcc": "",
            "bankIFSC": "", "bankBank": "", "qr": None, "note": "",
            "cod": False, "shippingFee": 0, "freeShippingAbove": 0
        }),))

    # ── Seed store settings ──
    if not db.execute("SELECT id FROM store_settings WHERE id=1").fetchone():
        db.execute("INSERT INTO store_settings (id,data) VALUES (1,?)", (json.dumps({
            "storeName": "MB Divine Jewels",
            "tagline": "Style, Starts Here",
            "announcement": "\u2726 Free Shipping on All Orders Across India \u2726",
            "heroEyebrow": "Welcome to MB Divine Jewels ",
            "heroTitle": "Jewellery That Feels Like You",
            "heroBtn": "Shop Collection \u2192",
            "feat1Title": "3 months warranty",   "feat1Sub": "for all product",
            "feat2Title": "Secure Payment",  "feat2Sub": "UPI / Bank",
            "feat3Title": "Quality Assured", "feat3Sub": "Premium Gold Plate",
            "feat4Title": "No refund",    "feat4Sub": "Only exchange",
            "footerTagline": "Style, Starts Here",
            "footerAddress": "Tamil Nadu, India",
            "whatsapp": "", "instagram": "mb_divine_jewels_",
            "shippingPolicy": "We offer free shipping on all orders across India. Orders are processed within 1-2 business days. Delivery typically takes 5-7 business days.",
            "refundPolicy": "We accept returns within 7 days of delivery if the product is damaged or defective. Refunds are processed within 5-7 business days.",
            "privacyPolicy": "We collect your name, phone, email, and address solely to process your order. Your information is never shared with third parties."
        }),))

    # ── Seed story ──
    if not db.execute("SELECT id FROM story_section WHERE id=1").fetchone():
        db.execute("INSERT INTO story_section (id,data) VALUES (1,?)", (json.dumps({
            "image": None,
            "title": "Soft Sparkles,\nEveryday Energy",
            "body": "MB Divine Jewels is all about the little details that make you feel like you. From minimal rings to delicate chains, every piece is designed to be elegant, effortless, and made for your daily moments.\n\nThink jewellery you can wear from morning rituals to late-night plans \u2014 soft, timeless, and always shining with you.",
            "btnText": "Our Story \u2726"
        }),))

    # ── Seed testimonials ──
    if not db.execute("SELECT id FROM testimonials_section WHERE id=1").fetchone():
        db.execute("INSERT INTO testimonials_section (id,data) VALUES (1,?)", (json.dumps({
            "items": [
                {"name": "Akshara", "location": "Chennai, TN",   "text": "I wear my MB Divine pieces literally every day \u2014 showers, coffee runs, everything. Still shiny and sooo cute!", "stars": 5},
                {"name": "Fayha",   "location": "Kozhikode, KL", "text": "Minimal but makes my whole outfit feel complete. The layering vibe is just perfect \u2728 \u2014 obsessed!", "stars": 5},
                {"name": "Hadiya",  "location": "Thrissur, KL",  "text": "Finally jewellery I don't have to remove all the time. Soft, pretty, and my daily go-to now.", "stars": 5}
            ]
        }),))

    # ── Seed gallery ──
    if not db.execute("SELECT id FROM gallery_section WHERE id=1").fetchone():
        db.execute("INSERT INTO gallery_section (id,data) VALUES (1,?)", (json.dumps({"images": []}),))

    # ── Seed categories ──
    if not db.execute("SELECT id FROM categories LIMIT 1").fetchone():
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Anti Tarnish Chains", 0))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Chokers", 1))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Earrings", 2))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Nose Pins", 3))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Second Studs", 4))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Anklets", 5))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Hand Chains", 6))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Rings", 7))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Charms", 8))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Plain Chains", 9))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Double Layer Chains", 10))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Kadas", 11))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Chain Bracelets", 12))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Hand Cuffs", 13))
        db.execute("INSERT OR IGNORE INTO categories (name,sort_order) VALUES (?,?)", ("Other", 14))

    db.commit()
    db.close()
