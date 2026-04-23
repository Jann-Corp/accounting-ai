from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import traceback

from app.core.config import settings
from app.core.logging import logger
from app.api import auth, wallets, categories, records, ai, stats, export, apikeys

# Run Alembic migrations on startup
def run_migrations():
    """Run alembic migrations on startup."""
    from alembic.config import Config as AlembicConfig
    from alembic.runtime.migration import MigrationContext
    from alembic.script import ScriptDirectory
    from sqlalchemy import create_engine
    
    try:
        db_url = os.environ.get("DATABASE_URL", str(settings.DATABASE_URL))
        engine = create_engine(db_url)
        
        # Get alembic config
        alembic_cfg = AlembicConfig("/app/alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        
        with engine.connect() as connection:
            context = MigrationContext.configure(
                connection=connection,
                opts={
                    'compare_type': True,
                    'render_as_batch': True,
                }
            )
            
            # Get current and head revisions
            current_rev = context.get_current_revision()
            head_rev = script.get_current_head()
            
            if current_rev != head_rev:
                logger.info(f"Running database migrations: {current_rev} -> {head_rev}")
                # Run migrations
                context.run_migrations()
                logger.info("Migrations completed successfully")
            else:
                logger.info("Database is up to date")
                
    except Exception as e:
        error_msg = f"Failed to run migrations: {e}\n{traceback.format_exc()}"
        logger.error(error_msg)

# Run migrations on startup
run_migrations()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI记账小程序后端 API",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
# NOTE: export router MUST be before records router because records has /{record_id} wildcard
app.include_router(auth.router, prefix="/api/v1")
app.include_router(wallets.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")  # Before records!
app.include_router(records.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(apikeys.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/")
def root():
    return {"message": "AI Accounting API", "version": "1.0.0"}
