from fastapi import HTTPException
from app.modules.legal_library.presentation.schemas.article_schemas import ArticleCreateRequest
from app.modules.legal_library.infrastructure.models import LegalArticle
from app.modules.legal_library.infrastructure.datasources.legal_datasource import PostgresLegalDatasource
from app.core.embeddings import engine as embedding_engine

class CreateArticleUseCase:
    def __init__(self, repository: PostgresLegalDatasource):
        self.repository = repository

    async def execute(self, request: ArticleCreateRequest) -> LegalArticle:
        # 1. Calcular embedding de forma asíncrona sin bloquear
        vector = await embedding_engine.generate_embedding(request.cuerpo_texto)
        
        # 2. Construir la entidad SQLModel usando los datos puros
        articleModel = LegalArticle(
            materia_juridica=request.materia_juridica,
            ley_o_codigo=request.ley_o_codigo,
            libro_o_titulo=request.libro_o_titulo,
            numero_articulo=request.numero_articulo,
            cuerpo_texto=request.cuerpo_texto,
            archivo_json_url=str(request.archivo_json_url),
            embedding=vector
        )
        
        # 3. Lanzar a infraestructura (este método ya captura los repetidos)
        try:
            return await self.repository.create_article(articleModel)
        except ValueError as e:
            # Domain exception traducida a HTTP de forma estandarizada global
            raise HTTPException(status_code=409, detail=str(e))
