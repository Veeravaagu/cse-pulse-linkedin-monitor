import logging

from fastapi import FastAPI

from app.api.routes import router
from app.config import settings

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))

app = FastAPI(title=settings.app_name)
app.include_router(router)
