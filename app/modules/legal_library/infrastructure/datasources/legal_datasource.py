from typing import Optional

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.legal_library.infrastructure.models import LegalArticle
from app.share.exceptions.base_exceptions import InfrastructureException


class LegalDatasource:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_article(self, article: LegalArticle) -> LegalArticle:
        try:
            self.db.add(article)
            await self.db.commit()
            await self.db.refresh(article)
            return article
        except IntegrityError:
            await self.db.rollback()
            return None
        except Exception as e:
            await self.db.rollback()
            raise InfrastructureException(
                message=f"Error al guardar el artículo en la base de datos: {str(e)}",
                code="DB_INSERT_ERROR",
            )

    async def get_article_by_id(self, article_id: int) -> Optional[LegalArticle]:
        statement = select(LegalArticle).where(LegalArticle.id == article_id)
        result = await self.db.exec(statement)
        return result.first()

    async def search_by_vector(
        self, query_vector: list[float], limit: int = 5
    ) -> list[dict]:
        """
        Búsqueda por similitud coseno usando el operador nativo de pgvector `<=>`.
        Retorna los artículos más cercanos al vector de consulta.
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

        result = await self.db.execute(
            sql, {"vector": str(query_vector), "limit": limit}
        )
        rows = result.fetchall()

        return [
            {
                "id": row.id,
                "materia_juridica": row.materia_juridica,
                "ley_o_codigo": row.ley_o_codigo,
                "libro_o_titulo": row.libro_o_titulo,
                "numero_articulo": row.numero_articulo,
                "cuerpo_texto": row.cuerpo_texto,
                "archivo_json_url": row.archivo_json_url,
                "similitud": round(float(row.similitud), 4),
            }
            for row in rows
        ]
