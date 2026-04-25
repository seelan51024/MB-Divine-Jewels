from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt, bcrypt, sqlite3, os, json, random, string, sys
from datetime import datetime, timedelta
from pathlib import Path

# Ensure backend package imports work whether app is started from the workspace root or from inside backend/
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from models import LoginRequest, ProductCreate, ProductUpdate, OrderCreate, CustomerOrderCreate, TokenResponse, UpdateStatusRequest, PaymentSettings, StoreSettings, StorySection, TestimonialsSection, GallerySection, ChangePasswordRequest
from database import get_db, init_db

app = FastAPI(title="MB Divine Jewels")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

JWT_SECRET = os.getenv("JWT_SECRET", "mbdivine_secret_2024")
security   = HTTPBearer()

@app.on_event("startup")
def startup(): init_db()

frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")

@app.get("/")
def serve_root(): return FileResponse(str(frontend_path / "customer.html"))

@app.get("/shop")
def serve_shop(): return FileResponse(str(frontend_path / "customer.html"))

@app.get("/admin")
def serve_admin(): return FileResponse(str(frontend_path / "index.html"))

# ── AUTH ──
def mk_token(email):
    return jwt.encode({"sub":email,"exp":datetime.utcnow()+timedelta(days=7)}, JWT_SECRET, algorithm="HS256")

def verify_token(creds: HTTPAuthorizationCredentials = Depends(security)):
    try: return jwt.decode(creds.credentials, JWT_SECRET, algorithms=["HS256"])["sub"]
    except jwt.ExpiredSignatureError: raise HTTPException(401,"Token expired")
    except: raise HTTPException(401,"Invalid token")

@app.post("/api/login", response_model=TokenResponse)
def login(body: LoginRequest, db=Depends(get_db)):
    row = db.execute("SELECT * FROM users WHERE email=?", (body.email,)).fetchone()
    if not row or not bcrypt.checkpw(body.password.encode(), row["password_hash"].encode()):
        raise HTTPException(401,"Invalid credentials")
    return {"token": mk_token(body.email), "email": body.email}

# ── PUBLIC (customer shop) ──
@app.get("/api/public/products")
def public_products(db=Depends(get_db)):
    return [dict(r) for r in db.execute(
        "SELECT id,name,price,stock,cat,mat,size,description,photo,photos FROM products WHERE stock>0 ORDER BY id ASC"
    ).fetchall()]

@app.post("/api/public/orders", status_code=201)
def public_order(body: CustomerOrderCreate, db=Depends(get_db)):
    # Stock check
    for item in body.items:
        row = db.execute("SELECT stock,name FROM products WHERE id=?", (int(item["id"]),)).fetchone()
        if not row: raise HTTPException(422, f"Product not found")
        if row["stock"] < item["qty"]:
            raise HTTPException(422, f"'{row['name']}' only {row['stock']} left in stock")
    oid = "ONL-" + ''.join(random.choices(string.ascii_uppercase+string.digits, k=6))
    db.execute(
        "INSERT INTO customer_orders (order_id,customer_name,customer_phone,customer_address,customer_note,items,total,shipping_fee,payment_method,payment_proof,payment_txn_id,time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (oid, body.customer_name, body.customer_phone, body.customer_address,
         body.customer_note or "", json.dumps(body.items), body.total,
         body.shipping_fee or 0, body.payment_method or "upi",
         body.payment_proof, body.payment_txn_id or "", body.time)
    )
    # Reduce stock immediately on order placement
    for item in body.items:
        pid = item.get("id")
        qty = item.get("qty", 1)
        if pid:
            db.execute("UPDATE products SET stock=MAX(0,stock-?) WHERE id=?", (qty, int(pid)))
    db.commit()
    return {"success": True, "order_id": oid}

# ── PUBLIC: Customer's own orders by phone ──
@app.get("/api/public/my-orders")
def get_my_orders(phone: str, db=Depends(get_db)):
    if not phone or len(phone.strip()) < 10:
        raise HTTPException(400, "Invalid phone number")
    rows = db.execute(
        "SELECT * FROM customer_orders WHERE customer_phone=? ORDER BY id DESC",
        (phone.strip(),)
    ).fetchall()
    return [dict(r, items=json.loads(r["items"])) for r in rows]

# ── PRODUCTS (admin) ──
@app.get("/api/products")
def get_products(user=Depends(verify_token), db=Depends(get_db)):
    return [dict(r) for r in db.execute("SELECT * FROM products ORDER BY id ASC").fetchall()]

@app.post("/api/products", status_code=201)
def create_product(body: ProductCreate, user=Depends(verify_token), db=Depends(get_db)):
    cur = db.execute(
        "INSERT INTO products (name,price,stock,cat,mat,size,description,photo,photos) VALUES (?,?,?,?,?,?,?,?,?)",
        (body.name,body.price,body.stock,body.cat,body.mat,body.size or "",body.description or "",body.photo,body.photos or '[]')
    )
    db.commit()
    return dict(db.execute("SELECT * FROM products WHERE id=?", (cur.lastrowid,)).fetchone())

@app.put("/api/products/{pid}")
def update_product(pid: int, body: ProductUpdate, user=Depends(verify_token), db=Depends(get_db)):
    db.execute(
        "UPDATE products SET name=?,price=?,stock=?,cat=?,mat=?,size=?,description=?,photo=?,photos=? WHERE id=?",
        (body.name,body.price,body.stock,body.cat,body.mat,body.size or "",body.description or "",body.photo,body.photos or '[]',pid)
    )
    db.commit()
    row = db.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if not row: raise HTTPException(404,"Product not found")
    return dict(row)

# ── PAYMENT SETTINGS ──
@app.get("/api/payment-settings")
def get_payment_settings(db=Depends(get_db)):
    row = db.execute("SELECT data FROM payment_settings WHERE id=1").fetchone()
    if row:
        d = json.loads(row["data"])
        d.pop("qr", None)  # Don't expose QR to public
        return d
    return {}

@app.get("/api/payment-settings/full")
def get_payment_settings_full(user=Depends(verify_token), db=Depends(get_db)):
    row = db.execute("SELECT data FROM payment_settings WHERE id=1").fetchone()
    return json.loads(row["data"]) if row else {}

@app.post("/api/payment-settings")
def save_payment_settings(body: PaymentSettings, user=Depends(verify_token), db=Depends(get_db)):
    db.execute("UPDATE payment_settings SET data=? WHERE id=1",
               (json.dumps(body.dict()),))
    db.commit()
    return {"success": True}

# ── PUBLIC PAYMENT SETTINGS (for customer page) ──
@app.get("/api/public/payment-settings")
def get_public_payment_settings(db=Depends(get_db)):
    row = db.execute("SELECT data FROM payment_settings WHERE id=1").fetchone()
    if not row: return {}
    d = json.loads(row["data"])
    # Don't expose full bank details publicly — just what customer needs
    return {"upi": d.get("upi",""), "upiName": d.get("upiName",""), "qr": d.get("qr"), "note": d.get("note",""), "cod": d.get("cod",False), "hasBankTransfer": bool(d.get("bankAcc","")), "shippingFee": d.get("shippingFee",0), "freeShippingAbove": d.get("freeShippingAbove",0)}


@app.delete("/api/products/{pid}")
def delete_product(pid: int, user=Depends(verify_token), db=Depends(get_db)):
    db.execute("DELETE FROM products WHERE id=?", (pid,))
    db.commit()
    return {"success": True}

# ── ORDERS (admin billing) ──
@app.get("/api/orders")
def get_orders(user=Depends(verify_token), db=Depends(get_db)):
    rows = db.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    return [dict(r, items=json.loads(r["items"])) for r in rows]

@app.post("/api/orders", status_code=201)
def create_order(body: OrderCreate, user=Depends(verify_token), db=Depends(get_db)):
    db.execute("INSERT INTO orders (order_id,items,total,pay,time) VALUES (?,?,?,?,?)",
               (body.id, json.dumps(body.items), body.total, body.pay, body.time))
    if body.cart:
        for pid, item in body.cart.items():
            db.execute("UPDATE products SET stock=MAX(0,stock-?) WHERE id=?", (item["qty"], int(pid)))
    db.commit()
    return {"success": True, "order_id": body.id}

@app.delete("/api/orders/{order_id}")
def delete_order(order_id: str, user=Depends(verify_token), db=Depends(get_db)):
    db.execute("DELETE FROM orders WHERE order_id=?", (order_id,))
    db.commit()
    return {"success": True}

# ── CUSTOMER ORDERS (admin view) ──
@app.get("/api/customer-orders")
def get_customer_orders(user=Depends(verify_token), db=Depends(get_db)):
    rows = db.execute("SELECT * FROM customer_orders ORDER BY id DESC").fetchall()
    return [dict(r, items=json.loads(r["items"])) for r in rows]

@app.put("/api/customer-orders/{order_id}/status")
def update_status(order_id: str, body: UpdateStatusRequest, user=Depends(verify_token), db=Depends(get_db)):
    row = db.execute("SELECT * FROM customer_orders WHERE order_id=?", (order_id,)).fetchone()
    if not row: raise HTTPException(404, "Order not found")
    # Stock is already reduced at order placement — no double reduction here
    db.execute("UPDATE customer_orders SET status=? WHERE order_id=?", (body.new_status, order_id))
    db.commit()
    return {"success": True}

@app.delete("/api/customer-orders/{order_id}")
def delete_customer_order(order_id: str, user=Depends(verify_token), db=Depends(get_db)):
    db.execute("DELETE FROM customer_orders WHERE order_id=?", (order_id,))
    db.commit()
    return {"success": True}


# ── STORE SETTINGS ──
@app.get("/api/store-settings")
def get_store_settings(db=Depends(get_db)):
    row = db.execute("SELECT data FROM store_settings WHERE id=1").fetchone()
    return json.loads(row["data"]) if row else {}

@app.post("/api/store-settings")
def save_store_settings(body: StoreSettings, user=Depends(verify_token), db=Depends(get_db)):
    db.execute("UPDATE store_settings SET data=? WHERE id=1", (json.dumps(body.dict()),))
    db.commit()
    return {"success": True}


# ── STORY SECTION ──
@app.get("/api/story-section")
def get_story(db=Depends(get_db)):
    row = db.execute("SELECT data FROM story_section WHERE id=1").fetchone()
    return json.loads(row["data"]) if row else {}

@app.post("/api/story-section")
def save_story(body: StorySection, user=Depends(verify_token), db=Depends(get_db)):
    db.execute("UPDATE story_section SET data=? WHERE id=1",(json.dumps(body.dict()),))
    db.commit()
    return {"success": True}

# ── TESTIMONIALS SECTION ──
@app.get("/api/testimonials-section")
def get_testimonials(db=Depends(get_db)):
    row = db.execute("SELECT data FROM testimonials_section WHERE id=1").fetchone()
    return json.loads(row["data"]) if row else {}

@app.post("/api/testimonials-section")
def save_testimonials(body: TestimonialsSection, user=Depends(verify_token), db=Depends(get_db)):
    db.execute("UPDATE testimonials_section SET data=? WHERE id=1",(json.dumps(body.dict()),))
    db.commit()
    return {"success": True}

# ── GALLERY SECTION ──
@app.get("/api/gallery-section")
def get_gallery(db=Depends(get_db)):
    row = db.execute("SELECT data FROM gallery_section WHERE id=1").fetchone()
    return json.loads(row["data"]) if row else {}

@app.post("/api/gallery-section")
def save_gallery(body: GallerySection, user=Depends(verify_token), db=Depends(get_db)):
    db.execute("UPDATE gallery_section SET data=? WHERE id=1",(json.dumps(body.dict()),))
    db.commit()
    return {"success": True}


# -- CHANGE PASSWORD --
@app.post("/api/change-password")
def change_password(body: ChangePasswordRequest, user=Depends(verify_token), db=Depends(get_db)):
    row = db.execute("SELECT * FROM users WHERE email=?", (user,)).fetchone()
    if not row: raise HTTPException(404,"User not found")
    if not bcrypt.checkpw(body.current_password.encode(), row["password_hash"].encode()):
        raise HTTPException(400,"Current password is incorrect")
    if len(body.new_password) < 6: raise HTTPException(400,"Password too short (min 6)")
    new_hash = bcrypt.hashpw(body.new_password.encode(), bcrypt.gensalt()).decode()
    db.execute("UPDATE users SET password_hash=? WHERE email=?", (new_hash, user))
    db.commit()
    return {"success": True}

# -- DASHBOARD STATS --
@app.get("/api/dashboard-stats")
def dashboard_stats(user=Depends(verify_token), db=Depends(get_db)):
    from datetime import date as _d
    today = _d.today().isoformat()
    pos_today = db.execute("SELECT COALESCE(SUM(total),0) as rev, COUNT(*) as cnt FROM orders WHERE time LIKE ?", (today+"%",)).fetchone()
    online_today = db.execute("SELECT COALESCE(SUM(total),0) as rev, COUNT(*) as cnt FROM customer_orders WHERE time LIKE ? AND status!='cancelled'", (today+"%",)).fetchone()
    all_pos = db.execute("SELECT COALESCE(SUM(total),0) as rev FROM orders").fetchone()
    all_online = db.execute("SELECT COALESCE(SUM(total),0) as rev FROM customer_orders WHERE status='completed'").fetchone()
    prods = db.execute("SELECT COUNT(*) as cnt, COALESCE(SUM(stock),0) as stock FROM products").fetchone()
    low_stock = db.execute("SELECT id,name,stock,price FROM products WHERE stock<=3 AND stock>0 ORDER BY stock ASC").fetchall()
    out_of_stock = db.execute("SELECT COUNT(*) as cnt FROM products WHERE stock=0").fetchone()
    pending = db.execute("SELECT COUNT(*) as cnt FROM customer_orders WHERE status='new'").fetchone()
    weekly_pos = db.execute("SELECT date(time) as day, SUM(total) as rev FROM orders WHERE date(time)>=date('now','-6 days') GROUP BY day ORDER BY day").fetchall()
    weekly_onl = db.execute("SELECT date(time) as day, SUM(total) as rev FROM customer_orders WHERE date(time)>=date('now','-6 days') AND status='completed' GROUP BY day ORDER BY day").fetchall()
    return {
        "today_revenue": (pos_today["rev"] or 0)+(online_today["rev"] or 0),
        "today_pos_orders": pos_today["cnt"] or 0,
        "today_online_orders": online_today["cnt"] or 0,
        "all_time_revenue": (all_pos["rev"] or 0)+(all_online["rev"] or 0),
        "total_products": prods["cnt"] or 0,
        "total_stock": prods["stock"] or 0,
        "low_stock": [dict(r) for r in low_stock],
        "out_of_stock_count": out_of_stock["cnt"] or 0,
        "pending_online_orders": pending["cnt"] or 0,
        "weekly_pos": [{"day":r["day"],"rev":r["rev"] or 0} for r in weekly_pos],
        "weekly_online": [{"day":r["day"],"rev":r["rev"] or 0} for r in weekly_onl],
    }



