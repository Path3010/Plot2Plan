"""
FastAPI Application Entry Point
Floor Plan Generator API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.api.routes import upload, generate, export, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    print(f"[START] Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[DIR] Upload directory: {settings.UPLOAD_DIR.absolute()}")
    print(f"[DIR] Export directory: {settings.EXPORT_DIR.absolute()}")
    yield
    # Shutdown
    print("[STOP] Shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## Floor Plan Generator API
    
    A rule-based architectural floor plan generation system that takes 
    plot boundary DXF files as input and generates multi-floor house plans.
    
    ### Features:
    - DXF file upload and parsing
    - Setback and buildable area calculation
    - Zone-based room allocation
    - Multi-floor plan generation
    - Layout scoring and optimization
    - DXF export with layered output
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(generate.router, prefix="/api", tags=["Generation"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(config.router, prefix="/api", tags=["Configuration"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
