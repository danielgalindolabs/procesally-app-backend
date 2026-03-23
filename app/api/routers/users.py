from fastapi import FastAPI
from app.modules.users.presentation.api.users_router import router as users_router

def add_routers(app: FastAPI):
    app.include_router(users_router, prefix="/api/v1/users", tags=["Gestión de Usuarios"])
