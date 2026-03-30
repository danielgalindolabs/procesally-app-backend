from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.legal_library.application.use_cases.bulk_ingest import (
    BulkIngestUseCase,
)
from app.modules.legal_library.application.use_cases.create_article import (
    CreateArticleUseCase,
)
from app.modules.legal_library.application.use_cases.search_articles import (
    SearchArticlesUseCase,
)
from app.modules.legal_library.infrastructure.datasources.legal_datasource import (
    PostgresLegalDatasource,
)
from app.share.infrastructure.db.session import get_session


def get_legal_repository(
    db: AsyncSession = Depends(get_session),
) -> PostgresLegalDatasource:
    return PostgresLegalDatasource(db)


def get_create_article_use_case(
    repository: PostgresLegalDatasource = Depends(get_legal_repository),
) -> CreateArticleUseCase:
    return CreateArticleUseCase(repository)


def get_search_articles_use_case(
    repository: PostgresLegalDatasource = Depends(get_legal_repository),
) -> SearchArticlesUseCase:
    return SearchArticlesUseCase(repository)


def get_bulk_ingest_use_case(
    repository: PostgresLegalDatasource = Depends(get_legal_repository),
) -> BulkIngestUseCase:
    return BulkIngestUseCase(repository)
