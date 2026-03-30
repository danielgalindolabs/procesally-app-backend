from app.modules.legal_library.infrastructure.datasources.legal_datasource import (
    PostgresLegalDatasource,
)
from app.modules.legal_library.presentation.schemas.article_schemas import SearchRequest
from app.share.exceptions.base_exceptions import InfrastructureException
from app.share.infrastructure.services.embedding_service import (
    engine as embedding_engine,
)


class SearchArticlesUseCase:
    def __init__(self, repository: PostgresLegalDatasource):
        self.repository = repository

    async def execute(self, request: SearchRequest) -> list[dict]:
        try:
            # 1. Convertir la consulta en lenguaje natural a un vector semántico
            query_vector = await embedding_engine.generate_embedding(request.consulta)

            # 2. Buscar los artículos más cercanos en el espacio vectorial
            return await self.repository.search_by_vector(query_vector, request.limite)
        except Exception as e:
            if "openai" in str(e).lower():
                raise  # Let the global handler catch OpenAI specific errors
            raise InfrastructureException(
                message=f"Error durante la búsqueda semántica: {str(e)}",
                code="SEARCH_ERROR",
            )
