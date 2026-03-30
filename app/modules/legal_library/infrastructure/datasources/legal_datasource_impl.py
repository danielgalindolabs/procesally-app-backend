from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import delete, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.legal_library.domain.datasources.legal_datasource import (
    DatasourceArticleInputDTO,
    DatasourceArticleOutputDTO,
    LegalDatasource,
)
from app.modules.legal_library.infrastructure.models import LegalArticle
from app.share.exceptions.base_exceptions import InfrastructureException


class LegalDatasourceImpl(LegalDatasource):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_article(
        self, ds_input: DatasourceArticleInputDTO
    ) -> Optional[DatasourceArticleOutputDTO]:
        try:
            # Construir modelo SQLModel desde el DTO del Datasource
            article_model = LegalArticle(
                materia_juridica=ds_input.materia_juridica,
                ley_o_codigo=ds_input.ley_o_codigo,
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
                libro_o_titulo=article_model.libro_o_titulo,
                numero_articulo=article_model.numero_articulo,
                cuerpo_texto=article_model.cuerpo_texto,
                archivo_json_url=article_model.archivo_json_url,
                embedding=article_model.embedding,
            )

        except IntegrityError:
            await self.db.rollback()
            return None
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
            libro_o_titulo=article_model.libro_o_titulo,
            numero_articulo=article_model.numero_articulo,
            cuerpo_texto=article_model.cuerpo_texto,
            archivo_json_url=article_model.archivo_json_url,
            embedding=article_model.embedding,
        )

    async def search_by_vector(
        self, vector: list[float], limit: int = 5
    ) -> list[DatasourceArticleOutputDTO]:
        """
        Búsqueda por similitud coseno usando el operador nativo de pgvector `<=>`.
        """
        sql = text("""
            SELECT
                id, materia_juridica, ley_o_codigo, libro_o_titulo,
                numero_articulo, cuerpo_texto, archivo_json_url,
                1 - (embedding <=> :vector) AS similitud
            FROM legal_articles
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :vector
            LIMIT :limit
        """)

        result = await self.db.execute(sql, {"vector": str(vector), "limit": limit})
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
                embedding=None,  # Optimization: Not always returning full embeddings on search
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
