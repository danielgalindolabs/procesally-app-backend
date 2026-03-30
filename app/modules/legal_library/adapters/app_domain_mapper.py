from typing import Optional

from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppInputDTO,
    ArticleAppOutputDTO,
)
from app.modules.legal_library.domain.entities.article_entity import ArticleEntity


class AppDomainMapper:
    @staticmethod
    def app_input_to_domain(
        app_dto: ArticleAppInputDTO, embedding: Optional[list[float]] = None
    ) -> ArticleEntity:
        return ArticleEntity(
            materia_juridica=app_dto.materia_juridica,
            ley_o_codigo=app_dto.ley_o_codigo,
            numero_articulo=app_dto.numero_articulo,
            cuerpo_texto=app_dto.cuerpo_texto,
            archivo_json_url=app_dto.archivo_json_url,
            libro_o_titulo=app_dto.libro_o_titulo,
            embedding=embedding,
        )

    @staticmethod
    def domain_to_app_output(entity: ArticleEntity) -> ArticleAppOutputDTO:
        return ArticleAppOutputDTO(
            id=entity.id,  # type: ignore
            materia_juridica=entity.materia_juridica,
            ley_o_codigo=entity.ley_o_codigo,
            numero_articulo=entity.numero_articulo,
            cuerpo_texto=entity.cuerpo_texto,
            archivo_json_url=entity.archivo_json_url,
            libro_o_titulo=entity.libro_o_titulo,
            similitud=entity.similitud,
        )
