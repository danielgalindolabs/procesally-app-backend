from typing import Optional

from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppInputDTO,
    ArticleAppOutputDTO,
    DocumentAppInputDTO,
)
from app.modules.legal_library.domain.entities.article_entity import ArticleEntity
from app.modules.legal_library.domain.entities.legal_document_entity import (
    LegalDocumentEntity,
)


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
            document_id=app_dto.document_id,
            libro_o_titulo=app_dto.libro_o_titulo,
            embedding=embedding,
        )

    @staticmethod
    def document_app_to_domain(app_dto: DocumentAppInputDTO) -> LegalDocumentEntity:
        return LegalDocumentEntity(
            titulo=app_dto.titulo,
            nombre_archivo=app_dto.nombre_archivo,
            url_oficial=app_dto.url_oficial,
            url_interna=app_dto.url_interna,
            fecha_publicacion=app_dto.fecha_publicacion,
            fecha_ultima_reforma=app_dto.fecha_ultima_reforma,
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
            document_id=entity.document_id,
            libro_o_titulo=entity.libro_o_titulo,
            similitud=entity.similitud,
        )
