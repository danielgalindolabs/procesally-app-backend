from app.core.logger import setup_logging
setup_logging()

from fastapi import FastAPI
from contextlib import asynccontextmanager

# Instalamos los middlewares y protectores en la aplicación
from app.api.middlewares.cors import setup_cors
from app.api.middlewares.exceptions import setup_exception_handlers
from app.config import settings
from app.api.routers import auth, users, legal

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

setup_cors(app)
setup_exception_handlers(app)


auth.add_routers(app)
users.add_routers(app)
legal.add_routers(app)

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok"}
