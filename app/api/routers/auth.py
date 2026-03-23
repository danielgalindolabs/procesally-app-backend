from fastapi import FastAPI
from app.modules.auth.presentation.api.auth_router import router as auth_router

def add_routers(app: FastAPI):
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Autenticación y Seguridad"])
