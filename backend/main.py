"""
Smart Invoice Generator — Main FastAPI Application
Entry point for the backend server.
"""

import os
from dotenv import load_dotenv
load_dotenv()

import sys
import ctypes.util

# ── macOS: Monkeypatch find_library for WeasyPrint/Homebrew ──────────────────
def _patch_weasyprint():
    if sys.platform != 'darwin': return
    orig_find_library = ctypes.util.find_library
    def my_find_library(name):
        lib_map = {
            'pango': 'libpango-1.0.0.dylib', 'pangocairo': 'libpangocairo-1.0.0.dylib',
            'cairo': 'libcairo.2.dylib', 'gobject': 'libgobject-2.0.0.dylib',
            'glib': 'libglib-2.0.0.dylib', 'harfbuzz': 'libharfbuzz.0.dylib',
            'harfbuzz-subset': 'libharfbuzz-subset.0.dylib',
            'fontconfig': 'libfontconfig.1.dylib', 'pangoft2': 'libpangoft2-1.0.0.dylib'
        }
        # Priority matching to avoid general names matching specific ones
        name_lower = name.lower()
        if 'pangoft2' in name_lower: 
            target = 'pangoft2'
        elif 'harfbuzz-subset' in name_lower:
            target = 'harfbuzz-subset'
        else:
            # Fallback to general map
            target = None
            for k in sorted(lib_map.keys(), key=len, reverse=True):
                if k in name.lower():
                    target = k
                    break
        
        if target:
            filename = lib_map[target]
            for base in ["/opt/homebrew/lib", "/usr/local/lib"]:
                path = os.path.join(base, filename)
                if os.path.exists(path):
                    print(f"DEBUG: Found {name} -> {path}")
                    return path
        res = orig_find_library(name)
        print(f"DEBUG: Search for {name} -> {res}")
        return res
    ctypes.util.find_library = my_find_library

_patch_weasyprint()

# ── Suppress Passlib/Bcrypt warning ──────────────────────────────────────────
try:
    import bcrypt
    if not hasattr(bcrypt, "__about__"):
        class About: pass
        About.__version__ = getattr(bcrypt, "__version__", "4.0.0")
        bcrypt.__about__ = About
except ImportError:
    pass

import uvicorn


from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from database import connect_to_mongo, close_mongo_connection
from config import settings

# Import routes
from auth import router as auth_router
from routes.invoices import router as invoices_router
from routes.ai_routes import router as ai_router
from routes.pdf import router as pdf_router
from routes.profile import router as profile_router
from routes.email_routes import router as email_router
from routes.org import router as org_router
from routes.clients import router as clients_router
from routes.analytics import router as analytics_router
from routes.design import router as design_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title=settings.APP_NAME,
    description="Backend API for Smart Invoice Generator",
    version="1.0.0",
    lifespan=lifespan
)

import traceback
from fastapi import Request
from fastapi.responses import JSONResponse

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        print("\n" + "!"*60)
        print("❌ CRITICAL EXCEPTION DETECTED")
        print(f"Path: {request.url.path}")
        print(f"Error: {str(e)}")
        print("-" * 30)
        traceback.print_exc()
        print("!"*60 + "\n")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(e)}", "traceback": traceback.format_exc()}
        )

# API Routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(invoices_router, prefix="/api/invoices", tags=["Invoices"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI Integration"])
app.include_router(pdf_router, prefix="/api/pdf", tags=["PDF"])
app.include_router(profile_router, prefix="/api/profile", tags=["Profile"])
app.include_router(email_router, prefix="/api/email", tags=["Email"])
app.include_router(org_router, prefix="/api/org", tags=["Organization Management"])
app.include_router(clients_router, prefix="/api/clients", tags=["Clients"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(design_router, prefix="/api/design", tags=["Design Engine"])

# Print registered routes for debugging
@app.on_event("startup")
async def debug_routes():
    print("\n--- REGISTERED ROUTES ---")
    for route in app.routes:
        if hasattr(route, 'path'):
            methods = getattr(route, 'methods', [])
            print(f"[{', '.join(methods)}] {route.path}")
    print("-------------------------\n")


# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


# Serve Frontend Static Files
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")

# Serve CSS, JS, Assets (Individual mounts for existing HTML links)
app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")
if os.path.exists(os.path.join(FRONTEND_DIR, "assets")):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

# User requested mount for /static
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# Serve HTML pages explicitly to remove .html extension in URLs
@app.get("/login")
async def serve_login():
    return FileResponse(os.path.join(FRONTEND_DIR, "login.html"))

@app.get("/dashboard")
async def serve_dashboard_explicit():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/create")
async def serve_create_invoice():
    return FileResponse(os.path.join(FRONTEND_DIR, "create.html"))

@app.get("/invoices")
async def serve_invoices_list():
    return FileResponse(os.path.join(FRONTEND_DIR, "invoices.html"))

@app.get("/settings")
async def serve_settings():
    return FileResponse(os.path.join(FRONTEND_DIR, "settings.html"))

@app.get("/org")
async def serve_org():
    return FileResponse(os.path.join(FRONTEND_DIR, "org.html"))

@app.get("/clients")
async def serve_clients():
    return FileResponse(os.path.join(FRONTEND_DIR, "clients.html"))

# Dashboard is the root
@app.get("/")
async def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
