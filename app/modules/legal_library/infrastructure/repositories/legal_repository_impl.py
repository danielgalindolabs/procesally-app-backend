from typing import Optional

from app.modules.legal_library.adapters.domain_datasource_mapper import (
    DomainDatasourceMapper,
)
from app.modules.legal_library.domain.datasources.legal_datasource import (
    LegalDatasource,
)
from app.modules.legal_library.domain.entities.article_entity import ArticleEntity
from app.modules.legal_library.domain.entities.legal_document_entity import (
    LegalDocumentEntity,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)


class LegalRepositoryImpl(LegalRepository):
    """
    Este es el Adaptador de Repositorio.
    Implementa el contrato del caso de uso (Domain).
    Delega la persistencia a un Datasource, transformando datos entre las fronteras.
    """

    def __init__(self, datasource: LegalDatasource):
        self.datasource = datasource

    async def create_document(
        self, document: LegalDocumentEntity
    ) -> LegalDocumentEntity:
        # 1. Mapear de Dominio a DTO de Datasource
        ds_input = DomainDatasourceMapper.document_domain_to_datasource_input(document)

        # 2. Invocar al datasource
        ds_output = await self.datasource.create_document(ds_input)

        # 3. Mapear de regreso a Dominio
        return DomainDatasourceMapper.document_datasource_output_to_domain(ds_output)

    async def create_article(self, article: ArticleEntity) -> Optional[ArticleEntity]:
        # 1. Mapear de Dominio a DTO esperado por el Datasource
        ds_input = DomainDatasourceMapper.domain_to_datasource_input(article)

        # 2. Invocar al datasource (Infraestructura concreta / Contrato)
        ds_output = await self.datasource.create_article(ds_input)

        if ds_output is None:
            return None

        # 3. Mapear de respuesta del Datasource de regreso a Dominio
        return DomainDatasourceMapper.datasource_output_to_domain(ds_output)

    async def get_article_by_id(self, article_id: int) -> Optional[ArticleEntity]:
        ds_output = await self.datasource.get_article_by_id(article_id)
        if ds_output is None:
            return None
        return DomainDatasourceMapper.datasource_output_to_domain(ds_output)

    async def get_articles_by_numbers(
        self, numbers: list[str], ley: str
    ) -> list[ArticleEntity]:
        ds_outputs = await self.datasource.get_articles_by_numbers(numbers, ley)
        return [
            DomainDatasourceMapper.datasource_output_to_domain(ds_output)
            for ds_output in ds_outputs
        ]

    async def search_similar_vectors(
        self,
        vector: list[float],
        limit: int = 5,
        materia_juridica: Optional[str] = None,
        ley_o_codigo: Optional[str] = None,
    ) -> list[ArticleEntity]:

        # Obtenemos los DTOs de Datasource (pueden venir de SQL, Mongo, Memoria, etc)
        ds_results = await self.datasource.search_by_vector(
            vector, limit, materia_juridica, ley_o_codigo
        )

        # Retornamos como entidades estrictas de negocio
        return [
            DomainDatasourceMapper.datasource_output_to_domain(ds_out)
            for ds_out in ds_results
        ]

    async def delete_articles_by_file(self, file_url: str) -> int:
        """Contrato de repositorio que delega al datasource."""
        return await self.datasource.delete_by_file(file_url)

    async def get_document_by_url(self, url: str) -> Optional[LegalDocumentEntity]:
        ds_output = await self.datasource.get_document_by_url(url)
        if ds_output is None:
            return None
        return DomainDatasourceMapper.document_datasource_output_to_domain(ds_output)

    async def get_document_by_title(self, title: str) -> Optional[LegalDocumentEntity]:
        ds_output = await self.datasource.get_document_by_title(title)
        if ds_output is None:
            return None
        return DomainDatasourceMapper.document_datasource_output_to_domain(ds_output)

    async def get_document_by_filename(self, filename: str) -> Optional[LegalDocumentEntity]:
        ds_output = await self.datasource.get_document_by_filename(filename)
        if ds_output is None:
            return None
        return DomainDatasourceMapper.document_datasource_output_to_domain(ds_output)

    async def delete_document(self, doc_id: int) -> bool:
        return await self.datasource.delete_document(doc_id)
