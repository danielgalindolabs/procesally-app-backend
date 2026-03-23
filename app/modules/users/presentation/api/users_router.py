from fastapi import APIRouter, Depends
from app.modules.users.domain.services import UserService

router = APIRouter()

@router.get("/me")
async def get_user_profile(user_service: UserService = Depends()):
    return await user_service.get_user_profile()
