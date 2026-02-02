from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.guests.routers import router as guests_router
from src.routers.healthz.router import router as healthz_router

app = FastAPI(
    title="Wedding RSVP API",
    description="API for managing wedding RSVPs and guest lists",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(healthz_router, prefix="/healthz", tags=["Healthz"])
app.include_router(guests_router, tags=["Guests"])


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Wedding RSVP API"}
