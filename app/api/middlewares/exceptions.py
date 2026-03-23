from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.modules.users.exceptions.user_exceptions import UserNotFoundError

def setup_exception_handlers(app: FastAPI):
    
    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(request: Request, exc: UserNotFoundError):
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "code": "USER_NOT_FOUND",
                "message": str(exc),
                "meta": {"requested_id": exc.user_id}
            }
        )
