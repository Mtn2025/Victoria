"""
Main Application Entry Point (HTTP Interface).
Aggregates all migrated endpoints.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from asgi_correlation_id import CorrelationIdMiddleware

from backend.infrastructure.config.settings import settings
from backend.infrastructure.database.session import engine
from backend.infrastructure.database.models import Base
from backend.interfaces.http.endpoints import telephony, config, history
from backend.interfaces.websocket.endpoints import audio_stream

# Configure logging (Simplified for now, or import from Core)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Starting Victoria Voice Orchestrator (New Architecture)...")
    
    # Ensure DB tables exist (Pragmatic approach for sqlite)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    await engine.dispose()

def create_app() -> FastAPI:
    app = FastAPI(
        title="Victoria Voice Orchestrator",
        description="Hexagonal Architecture Implementation",
        version="2.0.0",
        lifespan=lifespan
    )

    # Middleware
    from backend.infrastructure.security.headers import SecurityHeadersMiddleware
    from backend.infrastructure.security.core import setup_security
    
    setup_security(app) # Rate Limiting
    app.add_middleware(SecurityHeadersMiddleware) # Security Headers
    app.add_middleware(CorrelationIdMiddleware)
    
    # CORS: Load from settings in prod
    origins = ["http://localhost:5173", "http://localhost:3000"]
    # Add production domain if configured
    if settings.ENVIRONMENT == "production":
         # origins = ["https://app.victoria.ai"] # TODO: Configure real domain
         pass

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if settings.ENVIRONMENT == "production" else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount Routers
    # Mount Routers
    # Public (Webhooks need signature validation, handled internally)
    app.include_router(telephony.router)
    app.include_router(audio_stream.router)

    # Protected (Dashboard/API access)
    from backend.infrastructure.security.core import get_api_key
    from fastapi import Depends
    
    app.include_router(config.router, prefix="/api", dependencies=[Depends(get_api_key)]) 
    app.include_router(history.router, prefix="/api", dependencies=[Depends(get_api_key)])
    
    # Monitoring
    from backend.interfaces.http.endpoints import health
    app.include_router(health.router)

    # Prometheus (Setup but not exposed on public router safely without auth in prod)
    # Ideally should be on internal port or protected. For MVP, we expose /metrics.
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        Instrumentator().instrument(app).expose(app)
    except ImportError:
        logger.warning("Prometheus instrumentator not found. Skipping metrics.")

    @app.get("/")
    async def root():
        return {"service": "Victoria Voice Orchestrator", "version": "2.0.0", "docs": "/docs"}

    return app

app = create_app()
