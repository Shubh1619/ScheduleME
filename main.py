# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.db.database import Base, engine
from backend.routes import auth_routes, social_connect_routes, post_routes, analytics_routes, webhook_routes, healthcheck

settings = get_settings()

# Create tables (for dev; use migrations in prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(healthcheck.router, prefix=settings.API_V1_PREFIX)
app.include_router(auth_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(social_connect_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(post_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(analytics_routes.router, prefix=settings.API_V1_PREFIX)
app.include_router(webhook_routes.router, prefix=settings.API_V1_PREFIX)
