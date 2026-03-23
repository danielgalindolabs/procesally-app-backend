from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession
from app.share.infrastructure.db.session import get_session

from app.modules.legal_library.infrastructure.datasources.legal_datasource import PostgresLegalDatasource
from app.modules.legal_library.application.use_cases.create_article import CreateArticleUseCase

# Aquí construimos el árbol de dependencias
def get_legal_repository(db: AsyncSession = Depends(get_session)) -> PostgresLegalDatasource:
    return PostgresLegalDatasource(db)

def get_create_article_use_case(
    repository: PostgresLegalDatasource = Depends(get_legal_repository)
) -> CreateArticleUseCase:
    return CreateArticleUseCase(repository)
