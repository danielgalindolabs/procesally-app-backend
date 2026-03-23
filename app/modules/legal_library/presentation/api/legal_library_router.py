from fastapi import APIRouter, Depends, status

from app.modules.legal_library.presentation.schemas.article_schemas import ArticleCreateRequest, ArticleResponse
from app.modules.legal_library.application.use_cases.create_article import CreateArticleUseCase
from app.modules.legal_library.presentation.dependencies.legal_deps import get_create_article_use_case

router = APIRouter()

@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def upload_article(
    request: ArticleCreateRequest,
    create_uc: CreateArticleUseCase = Depends(get_create_article_use_case)
):
    """
    Ingesta un nuevo artículo legal en la biblioteca.
    - Calcula automáticamente su vector semántico en background
    - Guarda todos los metadatos relacionales
    - Rechaza inserciones si el 'Artículo' y la 'Ley' ya son exactamente los mismos
    """
    return await create_uc.execute(request)
