from typing import Optional

from sqlalchemy import text
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.legal_library.domain.datasources.legal_datasource import (
    DatasourceArticleInputDTO,
    DatasourceArticleOutputDTO,
    DatasourceDocumentInputDTO,
    DatasourceDocumentOutputDTO,
    LegalDatasource,
)
from app.modules.legal_library.infrastructure.models import LegalArticle, LegalDocument
from app.share.exceptions.base_exceptions import InfrastructureException


class LegalDatasourceImpl(LegalDatasource):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_document(
        self, ds_input: DatasourceDocumentInputDTO
    ) -> DatasourceDocumentOutputDTO:
        try:
            doc_model = LegalDocument(
                titulo=ds_input.titulo,
                nombre_archivo=ds_input.nombre_archivo,
                url_oficial=ds_input.url_oficial,
                url_interna=ds_input.url_interna,
                fecha_publicacion=ds_input.fecha_publicacion,
                fecha_ultima_reforma=ds_input.fecha_ultima_reforma,
            )
            self.db.add(doc_model)
            await self.db.commit()
            await self.db.refresh(doc_model)

            return DatasourceDocumentOutputDTO(
                id=doc_model.id,  # type: ignore
                titulo=doc_model.titulo,
                nombre_archivo=doc_model.nombre_archivo,
                url_oficial=doc_model.url_oficial,
                fecha_carga=doc_model.fecha_carga,
                url_interna=doc_model.url_interna,
                fecha_publicacion=doc_model.fecha_publicacion,
                fecha_ultima_reforma=doc_model.fecha_ultima_reforma,
            )
        except Exception as e:
            await self.db.rollback()
            raise InfrastructureException(
                message=f"Error al registrar el documento legal: {str(e)}",
                code="DB_DOC_INSERT_ERROR",
            )

    async def create_article(
        self, ds_input: DatasourceArticleInputDTO
    ) -> Optional[DatasourceArticleOutputDTO]:
        try:
            # Construir modelo SQLModel desde el DTO del Datasource
            article_model = LegalArticle(
                materia_juridica=ds_input.materia_juridica,
                ley_o_codigo=ds_input.ley_o_codigo,
                document_id=ds_input.document_id,
                libro_o_titulo=ds_input.libro_o_titulo,
                numero_articulo=ds_input.numero_articulo,
                cuerpo_texto=ds_input.cuerpo_texto,
                archivo_json_url=ds_input.archivo_json_url,
                embedding=ds_input.embedding,
            )

            self.db.add(article_model)
            await self.db.commit()
            await self.db.refresh(article_model)

            return DatasourceArticleOutputDTO(
                id=article_model.id,  # type: ignore
                materia_juridica=article_model.materia_juridica,
                ley_o_codigo=article_model.ley_o_codigo,
                document_id=article_model.document_id,
                libro_o_titulo=article_model.libro_o_titulo,
                numero_articulo=article_model.numero_articulo,
                cuerpo_texto=article_model.cuerpo_texto,
                archivo_json_url=article_model.archivo_json_url,
                embedding=article_model.embedding,
            )

        except Exception as e:
            await self.db.rollback()
            raise InfrastructureException(
                message=f"Error al guardar el artículo en la base de datos: {str(e)}",
                code="DB_INSERT_ERROR",
            )

    async def get_article_by_id(
        self, article_id: int
    ) -> Optional[DatasourceArticleOutputDTO]:
        statement = select(LegalArticle).where(LegalArticle.id == article_id)
        result = await self.db.exec(statement)
        article_model = result.first()

        if article_model is None:
            return None

        return DatasourceArticleOutputDTO(
            id=article_model.id,  # type: ignore
            materia_juridica=article_model.materia_juridica,
            ley_o_codigo=article_model.ley_o_codigo,
            document_id=article_model.document_id,
            libro_o_titulo=article_model.libro_o_titulo,
            numero_articulo=article_model.numero_articulo,
            cuerpo_texto=article_model.cuerpo_texto,
            archivo_json_url=article_model.archivo_json_url,
            embedding=article_model.embedding,
        )

    async def search_by_vector(
        self,
        vector: list[float],
        limit: int = 5,
        materia_juridica: Optional[str] = None,
        ley_o_codigo: Optional[str] = None,
    ) -> list[DatasourceArticleOutputDTO]:
        """
        Búsqueda por similitud coseno usando el operador nativo de pgvector `<=>`.
        Soporta filtrado dinámico por materia y ley.
        """
        query_parts = ["""
            SELECT
                id, materia_juridica, ley_o_codigo, libro_o_titulo,
                numero_articulo, cuerpo_texto, archivo_json_url,
                1 - (embedding <=> :vector) AS similitud
            FROM legal_articles
            WHERE embedding IS NOT NULL
            """]
        params = {"vector": str(vector), "limit": limit}

        if materia_juridica:
            query_parts.append("AND materia_juridica = :materia")
            params["materia"] = materia_juridica

        if ley_o_codigo:
            query_parts.append("AND ley_o_codigo = :ley")
            params["ley"] = ley_o_codigo

        query_parts.append("ORDER BY embedding <=> :vector LIMIT :limit")

        sql = text(" ".join(query_parts))

        result = await self.db.execute(sql, params)
        rows = result.fetchall()

        return [
            DatasourceArticleOutputDTO(
                id=row.id,
                materia_juridica=row.materia_juridica,
                ley_o_codigo=row.ley_o_codigo,
                libro_o_titulo=row.libro_o_titulo,
                numero_articulo=row.numero_articulo,
                cuerpo_texto=row.cuerpo_texto,
                archivo_json_url=row.archivo_json_url,
                embedding=None,
                similitud=round(float(row.similitud), 4),
            )
            for row in rows
        ]

    async def delete_by_file(self, file_url: str) -> int:
        """
        Elimina todos los registros que coincidan con archivo_json_url.
        """
        try:
            statement = delete(LegalArticle).where(
                LegalArticle.archivo_json_url == file_url
            )
            result = await self.db.exec(statement)
            await self.db.commit()
            return result.rowcount
        except Exception as e:
            await self.db.rollback()
            raise InfrastructureException(
                message=f"Error al eliminar artículos: {str(e)}",
                code="DB_DELETE_ERROR",
            )

    async def get_document_by_url(
        self, url: str
    ) -> Optional[DatasourceDocumentOutputDTO]:
        statement = select(LegalDocument).where(LegalDocument.url_oficial == url)
        result = await self.db.exec(statement)
        doc_model = result.first()

        if doc_model is None:
            return None

        return DatasourceDocumentOutputDTO(
            id=doc_model.id,  # type: ignore
            titulo=doc_model.titulo,
            nombre_archivo=doc_model.nombre_archivo,
            url_oficial=doc_model.url_oficial,
            fecha_carga=doc_model.fecha_carga,
            url_interna=doc_model.url_interna,
            fecha_publicacion=doc_model.fecha_publicacion,
            fecha_ultima_reforma=doc_model.fecha_ultima_reforma,
        )

    async def get_document_by_title(
        self, title: str
    ) -> Optional[DatasourceDocumentOutputDTO]:
        statement = select(LegalDocument).where(LegalDocument.titulo == title)
        result = await self.db.exec(statement)
        doc_model = result.first()

        if doc_model is None:
            return None

        return DatasourceDocumentOutputDTO(
            id=doc_model.id,  # type: ignore
            titulo=doc_model.titulo,
            nombre_archivo=doc_model.nombre_archivo,
            url_oficial=doc_model.url_oficial,
            fecha_carga=doc_model.fecha_carga,
            url_interna=doc_model.url_interna,
            fecha_publicacion=doc_model.fecha_publicacion,
            fecha_ultima_reforma=doc_model.fecha_ultima_reforma,
        )

    async def get_document_by_filename(
        self, filename: str
    ) -> Optional[DatasourceDocumentOutputDTO]:
        statement = select(LegalDocument).where(LegalDocument.nombre_archivo == filename)
        result = await self.db.exec(statement)
        doc_model = result.first()

        if doc_model is None:
            return None

        return DatasourceDocumentOutputDTO(
            id=doc_model.id,  # type: ignore
            titulo=doc_model.titulo,
            nombre_archivo=doc_model.nombre_archivo,
            url_oficial=doc_model.url_oficial,
            fecha_carga=doc_model.fecha_carga,
            url_interna=doc_model.url_interna,
            fecha_publicacion=doc_model.fecha_publicacion,
            fecha_ultima_reforma=doc_model.fecha_ultima_reforma,
        )

    async def delete_document(self, doc_id: int) -> bool:
        try:
            # 1. Eliminar artículos asociados primero
            art_statement = delete(LegalArticle).where(
                LegalArticle.document_id == doc_id
            )
            await self.db.exec(art_statement)

            # 2. Eliminar el documento
            doc_statement = delete(LegalDocument).where(LegalDocument.id == doc_id)
            await self.db.exec(doc_statement)

            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise InfrastructureException(
                message=f"Error al eliminar el documento y sus artículos: {str(e)}",
                code="DB_DELETE_ERROR",
            )
