from app.modules.legal_library.domain.datasources.legal_datasource import (
    DatasourceArticleInputDTO, DatasourceArticleOutputDTO,
    DatasourceDocumentInputDTO, DatasourceDocumentOutputDTO)
from app.modules.legal_library.domain.entities.article_entity import \
    ArticleEntity
from app.modules.legal_library.domain.entities.legal_document_entity import \
    LegalDocumentEntity


class DomainDatasourceMapper:
    @staticmethod
    def document_domain_to_datasource_input(
        entity: LegalDocumentEntity,
    ) -> DatasourceDocumentInputDTO:
        return DatasourceDocumentInputDTO(
            titulo=entity.titulo,
            nombre_archivo=entity.nombre_archivo,
            url_oficial=entity.url_oficial,
            url_interna=entity.url_interna,
            fecha_publicacion=entity.fecha_publicacion,
            fecha_ultima_reforma=entity.fecha_ultima_reforma,
        )

    @staticmethod
    def document_datasource_output_to_domain(
        ds_output: DatasourceDocumentOutputDTO,
    ) -> LegalDocumentEntity:
        return LegalDocumentEntity(
            id=ds_output.id,
            titulo=ds_output.titulo,
            nombre_archivo=ds_output.nombre_archivo,
            url_oficial=ds_output.url_oficial,
            url_interna=ds_output.url_interna,
            fecha_carga=ds_output.fecha_carga,
            fecha_publicacion=ds_output.fecha_publicacion,
            fecha_ultima_reforma=ds_output.fecha_ultima_reforma,
        )

    @staticmethod
    def domain_to_datasource_input(entity: ArticleEntity) -> DatasourceArticleInputDTO:
        return DatasourceArticleInputDTO(
            materia_juridica=entity.materia_juridica,
            ley_o_codigo=entity.ley_o_codigo,
            numero_articulo=entity.numero_articulo,
            cuerpo_texto=entity.cuerpo_texto,
            archivo_json_url=entity.archivo_json_url,
            document_id=entity.document_id,
            libro_o_titulo=entity.libro_o_titulo,
            embedding=entity.embedding,
        )

    @staticmethod
    def datasource_output_to_domain(
        ds_output: DatasourceArticleOutputDTO,
    ) -> ArticleEntity:
        return ArticleEntity(
            id=ds_output.id,
            materia_juridica=ds_output.materia_juridica,
            ley_o_codigo=ds_output.ley_o_codigo,
            numero_articulo=ds_output.numero_articulo,
            cuerpo_texto=ds_output.cuerpo_texto,
            archivo_json_url=ds_output.archivo_json_url,
            document_id=ds_output.document_id,
            libro_o_titulo=ds_output.libro_o_titulo,
            embedding=ds_output.embedding,
            similitud=ds_output.similitud,
        )
