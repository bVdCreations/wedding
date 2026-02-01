
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.settings import settings
from src.routers import guests, healthz, rsvp

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
app.include_router(healthz, prefix="/healthz", tags=["Health"])
app.include_router(guests, prefix="/guests", tags=["Guests"])
app.include_router(rsvp, prefix="/rsvp", tags=["RSVP"])


@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Wedding RSVP API"}
