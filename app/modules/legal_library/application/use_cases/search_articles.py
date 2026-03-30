from app.modules.legal_library.adapters.app_domain_mapper import AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppOutputDTO,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)
from app.modules.legal_library.domain.services.embedding_service import (
    EmbeddingService,
)
from app.modules.legal_library.domain.services.legal_router_service import (
    LegalRouterService,
)
from app.share.exceptions.base_exceptions import InfrastructureException


class SearchArticlesUseCase:
    """Caso de uso orquestador para la búsqueda semántica.
    Depende EXCLUSIVAMENTE de contratos de dominio.
    """

    def __init__(
        self,
        repository: LegalRepository,
        embedding_service: EmbeddingService,
        router_service: LegalRouterService,
    ):
        self.repository = repository
        self.embedding_service = embedding_service
        self.router_service = router_service

    async def execute(
        self,
        consulta: str,
        limite: int,
        materia_juridica: str | None = None,
        ley_o_codigo: str | None = None,
    ) -> list[ArticleAppOutputDTO]:
        try:
            # 1. Router: Si no hay materia_juridica explícita, intentamos detectarla
            if not materia_juridica:
                materia_juridica = await self.router_service.detect_materia(consulta)

            # 2. Convertir la consulta textual a vector semántico
            query_vector = await self.embedding_service.generate_embedding(consulta)

            # 3. Buscar Entidades de Dominio en el repositorio con filtros
            entities = await self.repository.search_similar_vectors(
                query_vector,
                limite,
                materia_juridica=materia_juridica,
                ley_o_codigo=ley_o_codigo,
            )

            # 4. Mapear de vuelta a DTOs de Aplicación
            return [AppDomainMapper.domain_to_app_output(e) for e in entities]

        except Exception as e:
            if "openai" in str(e).lower():
                raise
            raise InfrastructureException(
                message=f"Error durante la búsqueda semántica: {str(e)}",
                code="SEARCH_ERROR",
            )
