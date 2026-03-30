from app.modules.legal_library.adapters.app_domain_mapper import AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppOutputDTO,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)
from app.modules.legal_library.domain.services.embedding_service import EmbeddingService
from app.share.exceptions.base_exceptions import InfrastructureException


class SearchArticlesUseCase:
    """Caso de uso orquestador para la búsqueda semántica.
    Depende EXCLUSIVAMENTE de contratos de dominio.
    """

    def __init__(
        self, repository: LegalRepository, embedding_service: EmbeddingService
    ):
        self.repository = repository
        self.embedding_service = embedding_service

    async def execute(self, consulta: str, limite: int) -> list[ArticleAppOutputDTO]:
        try:
            # 1. Convertir la consulta textual a vector semántico usando el servicio de dominio
            query_vector = await self.embedding_service.generate_embedding(consulta)

            # 2. Buscar Entidades de Dominio en el repositorio
            entities = await self.repository.search_similar_vectors(
                query_vector, limite
            )

            # 3. Mapear de vuelta a DTOs de Aplicación
            return [AppDomainMapper.domain_to_app_output(e) for e in entities]

        except Exception as e:
            if "openai" in str(e).lower():
                raise
            raise InfrastructureException(
                message=f"Error durante la búsqueda semántica: {str(e)}",
                code="SEARCH_ERROR",
            )
