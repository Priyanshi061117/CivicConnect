from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # Register SQLAlchemy models
from app.api.auth import router as auth_router
from app.api.complaints import router as complaints_router
from app.api.phase5 import router as phase5_router
from app.db.session import Base, engine


app = FastAPI(
    title="AI Civic Complaint Router API",
    description="Backend API for the AI Civic Complaint Router project.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    # Creates missing tables only. It does not migrate existing columns.
    Base.metadata.create_all(bind=engine)


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "AI Civic Complaint Router API is running",
        "phase": 5,
    }


@app.get("/health/db", tags=["Health"])
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"database": "connected"}


app.include_router(auth_router)

# Register history before the generic /api/complaints/{complaint_id} route.
app.include_router(phase5_router)
app.include_router(complaints_router)