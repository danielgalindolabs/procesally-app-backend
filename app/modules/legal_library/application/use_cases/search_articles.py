from app.modules.legal_library.presentation.schemas.article_schemas import SearchRequest
from app.modules.legal_library.infrastructure.datasources.legal_datasource import PostgresLegalDatasource
from app.core.embeddings import engine as embedding_engine

class SearchArticlesUseCase:
    def __init__(self, repository: PostgresLegalDatasource):
        self.repository = repository

    async def execute(self, request: SearchRequest) -> list[dict]:
        # 1. Convertir la consulta en lenguaje natural a un vector semántico
        query_vector = await embedding_engine.generate_embedding(request.consulta)
        
        # 2. Buscar los artículos más cercanos en el espacio vectorial
        results = await self.repository.search_by_vector(query_vector, request.limite)
        
        return results
