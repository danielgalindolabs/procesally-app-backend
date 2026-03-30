from app.modules.legal_library.adapters.app_domain_mapper import AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppInputDTO,
    ArticleAppOutputDTO,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)
from app.modules.legal_library.domain.services.embedding_service import EmbeddingService
from app.modules.legal_library.exceptions.legal_exceptions import DuplicateArticleError


class CreateArticleUseCase:
    """Caso de uso orquestador para la creación de artículos.
    Depende EXCLUSIVAMENTE de contratos de dominio e inyecta DTOs de Aplicación.
    """

    def __init__(
        self, repository: LegalRepository, embedding_service: EmbeddingService
    ):
        self.repository = repository
        self.embedding_service = embedding_service

    async def execute(self, request_dto: ArticleAppInputDTO) -> ArticleAppOutputDTO:
        # 1. Usar contrato de dominio para calcular embedding de forma asíncrona
        vector = await self.embedding_service.generate_embedding(
            request_dto.cuerpo_texto
        )

        # 2. Convertir el App DTO a Entidad de Dominio
        article_entity = AppDomainMapper.app_input_to_domain(request_dto, vector)

        # 3. Lanzar a repositorio de Dominio
        saved_entity = await self.repository.create_article(article_entity)

        if saved_entity is None:
            raise DuplicateArticleError(
                request_dto.numero_articulo, request_dto.ley_o_codigo
            )

        # 4. Mapear Entidad resultante de vuelta a DTO de App
        return AppDomainMapper.domain_to_app_output(saved_entity)
