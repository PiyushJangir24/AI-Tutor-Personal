from __future__ import annotations

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import router
from app.config import settings
from app.errors import register_exception_handlers

app = FastAPI(title="Autonomous AI Tutor Orchestrator", version="0.1.0")

# CORS
origins = [o.strip() for o in (settings.cors_origins or "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)

# Error handlers
register_exception_handlers(app)


@app.get("/")
def root():
    return {"name": "Autonomous AI Tutor Orchestrator", "docs": "/docs"}
