from fastapi import FastAPI, Request
from app.api import vector, recommend
from app.logger import setup_logging
from app.middleware.log_middleware import LoggingMiddleware
import logging
import time
import json


setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(LoggingMiddleware)

app.include_router(vector.router, prefix="/api")
app.include_router(recommend.router, prefix="/api")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}