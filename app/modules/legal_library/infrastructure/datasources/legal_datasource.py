from typing import Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from sqlalchemy.exc import IntegrityError
from app.modules.legal_library.infrastructure.models import LegalArticle

class PostgresLegalDatasource:
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
            raise ValueError(f"El artículo '{article.numero_articulo}' de la ley '{article.ley_o_codigo}' ya existe en la biblioteca.")

    async def get_article_by_id(self, article_id: int) -> Optional[LegalArticle]:
        statement = select(LegalArticle).where(LegalArticle.id == article_id)
        result = await self.db.exec(statement)
        return result.first()
