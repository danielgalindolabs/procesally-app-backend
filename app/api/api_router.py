from fastapi import APIRouter

from app.modules.auth.presentation.api.auth_router import router as auth_router
from app.modules.legal_library.presentation.api.legal_library_router import \
    router as legal_router
from app.modules.users.presentation.api.users_router import \
    router as users_router

api_router = APIRouter()

api_router.include_router(
    auth_router, prefix="/api/v1/auth", tags=["Autenticación y Seguridad"]
)
api_router.include_router(
    users_router, prefix="/api/v1/users", tags=["Gestión de Usuarios"]
)
api_router.include_router(
    legal_router, prefix="/api/v1/legal", tags=["Inteligencia Artificial (RAG)"]
)
