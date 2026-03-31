from fastapi import Depends
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.legal_library.application.use_cases.bulk_ingest import (
    BulkIngestUseCase,
)
from app.modules.legal_library.application.use_cases.bulk_url_ingest import (
    BulkUrlIngestUseCase,
)
from app.modules.legal_library.application.use_cases.create_article import (
    CreateArticleUseCase,
)
from app.modules.legal_library.application.use_cases.delete_file import (
    DeleteFileUseCase,
)
from app.modules.legal_library.application.use_cases.parse_html_index import (
    ParseHtmlIndexUseCase,
)
from app.modules.legal_library.application.use_cases.search_articles import (
    SearchArticlesUseCase,
)
from app.modules.legal_library.domain.datasources.legal_datasource import (
    LegalDatasource,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)
from app.modules.legal_library.domain.services.document_downloader import (
    DocumentDownloader,
)
from app.modules.legal_library.domain.services.document_parser import DocumentParser
from app.modules.legal_library.domain.services.embedding_service import EmbeddingService
from app.modules.legal_library.domain.services.legal_router_service import (
    LegalRouterService,
)
from app.modules.legal_library.infrastructure.datasources.legal_datasource_impl import (
    LegalDatasourceImpl,
)
from app.modules.legal_library.infrastructure.repositories.legal_repository_impl import (
    LegalRepositoryImpl,
)
from app.modules.legal_library.infrastructure.services.embedding_service_impl import (
    OpenAIEmbeddingService,
)
from app.modules.legal_library.infrastructure.services.legal_router_service_impl import (
    LegalRouterServiceImpl,
)
from app.share.infrastructure.db.session import get_session
from app.share.infrastructure.http_client import HTTPClient
from app.share.infrastructure.parsers.dof_parser import DOFHtmlParser


def get_legal_datasource(
    db: AsyncSession = Depends(get_session),
) -> LegalDatasource:
    return LegalDatasourceImpl(db)


def get_legal_repository(
    datasource: LegalDatasource = Depends(get_legal_datasource),
) -> LegalRepository:
    return LegalRepositoryImpl(datasource)


def get_embedding_service() -> EmbeddingService:
    return OpenAIEmbeddingService()


def get_document_parser() -> DocumentParser:
    return DOFHtmlParser()


def get_router_service() -> LegalRouterService:
    return LegalRouterServiceImpl()


def get_http_client() -> DocumentDownloader:
    return HTTPClient()


def get_create_article_use_case(
    repository: LegalRepository = Depends(get_legal_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
) -> CreateArticleUseCase:
    return CreateArticleUseCase(repository, embedding_service)


def get_search_articles_use_case(
    repository: LegalRepository = Depends(get_legal_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    router_service: LegalRouterService = Depends(get_router_service),
) -> SearchArticlesUseCase:
    return SearchArticlesUseCase(repository, embedding_service, router_service)


def get_bulk_ingest_use_case(
    repository: LegalRepository = Depends(get_legal_repository),
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    document_parser: DocumentParser = Depends(get_document_parser),
) -> BulkIngestUseCase:
    return BulkIngestUseCase(repository, embedding_service, document_parser)


def get_delete_file_use_case(
    repository: LegalRepository = Depends(get_legal_repository),
) -> DeleteFileUseCase:
    return DeleteFileUseCase(repository)


def get_bulk_url_ingest_use_case(
    bulk_ingest_uc: BulkIngestUseCase = Depends(get_bulk_ingest_use_case),
    document_downloader: DocumentDownloader = Depends(get_http_client),
) -> BulkUrlIngestUseCase:
    return BulkUrlIngestUseCase(bulk_ingest_uc, document_downloader)


def get_parse_html_index_use_case() -> ParseHtmlIndexUseCase:
    return ParseHtmlIndexUseCase()
