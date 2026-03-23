from fastapi import APIRouter, Depends
from app.modules.auth.domain.services import AuthService

router = APIRouter()

@router.post("/login")
def login(auth_service: AuthService = Depends()):
    """
    Capa de Presentación (Auth). 
    Exclusiva para recibir peticiones web HTTP y mapear el JSON al dominio.
    """
    return auth_service.login_user()
