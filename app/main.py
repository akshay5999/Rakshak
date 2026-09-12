from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables

# Models
from app.models.soldier import Soldier
from app.models.wellbeing import WellbeingRecord
from app.models.sos import SOSAlert
from app.models.facial_scan import FacialScan

# Routes
from app.routes.soldier import router as soldier_router
from app.routes.sos import router as sos_router
from app.routes.ai import router as ai_router
from app.routes.wellbeing import router as wellbeing_router
from app.routes.alerts import router as alerts_router
from app.routes.facial_scan import router as facial_scan_router
from app.routes.stress_assessment import router as stress_assessment_router


app = FastAPI(
    title="RakshakCare API",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://172.26.92.246:5173",
        "http://172.26.92.246:5174",

        # Production frontend
        "https://rakshak-frontend-272n.vercel.app",
        "https://rakshak-frontend-272n-git-main-innovators2.vercel.app",
        "https://rakshak-frontend-272n-otcgojbws-innovators2.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# DATABASE STARTUP
# =========================================================

@app.on_event("startup")
def startup():
    """
    Create all missing database tables when backend starts.
    """

    create_tables()


# =========================================================
# API ROUTES
# =========================================================

# Soldier APIs
app.include_router(soldier_router)

# SOS / Emergency APIs
app.include_router(sos_router)

# AI Assistant / AI APIs
app.include_router(ai_router)

# Wellbeing APIs
app.include_router(wellbeing_router)

# Intelligent Alerts APIs
app.include_router(alerts_router)

# Facial Scan APIs
app.include_router(facial_scan_router)

# Final Stress Assessment APIs
app.include_router(stress_assessment_router)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():
    return {
        "message": "RakshakCare API is running",
        "status": "online",
        "service": "RakshakCare Backend",
        "version": "1.0.0"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "api": "online"
    }
