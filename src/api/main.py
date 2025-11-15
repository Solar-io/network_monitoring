"""FastAPI main application."""
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import config_view, dashboard, heartbeat, hosts
from src.config import get_settings
from src.database import init_db

# Configure logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting Network Monitoring API")
    logger.info(f"Initializing database: {settings.database_url}")
    init_db()
    logger.info("Database initialized")

    yield

    # Shutdown
    logger.info("Shutting down Network Monitoring API")


# Create FastAPI app
app = FastAPI(
    title="Network Monitoring System",
    description="Heartbeat monitoring, log analysis, and internet connectivity tracking",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(heartbeat.router, prefix="/api/v1", tags=["heartbeat"])
app.include_router(hosts.router, prefix="/api/v1", tags=["hosts"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["dashboard"])
app.include_router(config_view.router, prefix="/api/v1", tags=["configuration"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Network Monitoring System",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": "connected",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )
