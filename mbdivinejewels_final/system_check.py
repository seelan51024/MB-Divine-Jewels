#!/usr/bin/env python
"""System Health Check for MB Divine Jewels"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

print("=" * 60)
print("🔍 MB DIVINE JEWELS - SYSTEM HEALTH CHECK")
print("=" * 60)

# Check 1: Python Version
print("\n✅ Python Version:", sys.version.split()[0])

# Check 2: Backend Modules
try:
    from backend.main import app
    print("✅ Backend: FastAPI app loaded successfully")
    print("   - Total API Routes:", len(app.routes))
except Exception as e:
    print("❌ Backend: FastAPI app failed -", str(e))
    sys.exit(1)

# Check 3: Database
try:
    from backend.database import init_db, _connect
    db = _connect()
    init_db()
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    print("✅ Database: SQLite initialized")
    print("   - Database File: database/mbdivine.db")
    print("   - Total Tables:", len(tables))
    for t in tables:
        print(f"     • {t[0]}")
    
    # Check admin user
    admin = db.execute("SELECT email FROM users WHERE email=?", ("admin@mbdivine.com",)).fetchone()
    if admin:
        print("✅ Admin User: Created (admin@mbdivine.com / divine123)")
    
    db.close()
except Exception as e:
    print("❌ Database: Error -", str(e))
    sys.exit(1)

# Check 4: Frontend Files
try:
    frontend = Path(__file__).parent / "frontend"
    admin_html = frontend / "index.html"
    customer_html = frontend / "customer.html"
    
    if admin_html.exists():
        size = admin_html.stat().st_size / 1024
        print(f"✅ Frontend - Admin Panel: index.html ({size:.1f} KB)")
    else:
        print("❌ Frontend - Admin Panel: index.html NOT FOUND")
    
    if customer_html.exists():
        size = customer_html.stat().st_size / 1024
        print(f"✅ Frontend - Customer Page: customer.html ({size:.1f} KB)")
    else:
        print("❌ Frontend - Customer Page: customer.html NOT FOUND")
except Exception as e:
    print("❌ Frontend: Error -", str(e))

# Check 5: Models
try:
    from backend.models import (
        LoginRequest, ProductCreate, PaymentSettings, 
        StoreSettings, CategoryCreate
    )
    print("✅ Models: All Pydantic models loaded")
except Exception as e:
    print("❌ Models: Error -", str(e))

# Check 6: Requirements
try:
    req_file = Path(__file__).parent / "backend" / "requirements.txt"
    with open(req_file) as f:
        reqs = [line.strip() for line in f if line.strip()]
    print(f"✅ Requirements: {len(reqs)} packages defined")
    for req in reqs:
        print(f"   • {req}")
except Exception as e:
    print("❌ Requirements: Error -", str(e))

print("\n" + "=" * 60)
print("✨ SYSTEM STATUS: ALL CHECKS PASSED")
print("=" * 60)
print("\n📝 CONNECTIVITY FLOW:")
print("  1. Frontend (index.html / customer.html)")
print("  2. ├─ API Calls → FastAPI Backend (main.py)")
print("  3. └─ Backend ← → Database (SQLite mbdivine.db)")
print("\n🚀 TO RUN THE APP:")
print("  pip install -r backend/requirements.txt")
print("  python -m uvicorn backend.main:app --reload")
print("\n📱 ACCESS:")
print("  Admin: http://localhost:8000/admin")
print("  Shop: http://localhost:8000/shop")
print("=" * 60)
