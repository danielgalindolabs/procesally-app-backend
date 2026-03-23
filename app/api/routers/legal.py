from fastapi import FastAPI
from app.modules.legal_library.presentation.api.legal_library_router import router as legal_router

def add_routers(app: FastAPI):
    app.include_router(legal_router, prefix="/api/v1/legal", tags=["Inteligencia Artificial (RAG)"])
