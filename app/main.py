from app.core.logger import setup_logging

setup_logging()

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.api_router import api_router

# Instalamos los middlewares y protectores en la aplicación
from app.api.middlewares.cors import setup_cors
from app.core.config import settings
from app.core.exceptions.global_handlers import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, lifespan=lifespan)

setup_cors(app)
setup_exception_handlers(app)


app.include_router(api_router)


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok"}
