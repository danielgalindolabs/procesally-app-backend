from app.modules.legal_library.domain.datasources.legal_datasource import (
    DatasourceArticleInputDTO,
    DatasourceArticleOutputDTO,
)
from app.modules.legal_library.domain.entities.article_entity import ArticleEntity


class DomainDatasourceMapper:
    @staticmethod
    def domain_to_datasource_input(entity: ArticleEntity) -> DatasourceArticleInputDTO:
        return DatasourceArticleInputDTO(
            materia_juridica=entity.materia_juridica,
            ley_o_codigo=entity.ley_o_codigo,
            numero_articulo=entity.numero_articulo,
            cuerpo_texto=entity.cuerpo_texto,
            archivo_json_url=entity.archivo_json_url,
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
            libro_o_titulo=ds_output.libro_o_titulo,
            embedding=ds_output.embedding,
            similitud=ds_output.similitud,
        )
