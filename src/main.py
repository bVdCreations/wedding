from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config.database import Base, engine
from src.config.settings import settings
from src.routers import guests, healthz, rsvp


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: Close database connections
    await engine.dispose()


app = FastAPI(
    title="Wedding RSVP API",
    description="API for managing wedding RSVPs and guest lists",
    version="0.1.0",
    lifespan=lifespan,
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
