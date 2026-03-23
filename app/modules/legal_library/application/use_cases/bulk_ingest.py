import logging
from fastapi import HTTPException

from app.modules.legal_library.infrastructure.models import LegalArticle
from app.modules.legal_library.infrastructure.datasources.legal_datasource import PostgresLegalDatasource
from app.core.dof_parser import dof_parser
from app.core.embeddings import engine as embedding_engine

logger = logging.getLogger("app.legal_library.use_cases.bulk_ingest")


class BulkIngestUseCase:
    def __init__(self, repository: PostgresLegalDatasource):
        self.repository = repository

    async def execute(self, html_content: str, archivo_url: str) -> dict:
        # 1. Parsear el HTML con el parser determinístico
        parsed_articles = dof_parser.parse(html_content)

        if not parsed_articles:
            raise HTTPException(status_code=422, detail="No se pudieron extraer artículos del archivo HTML. Verifica que sea un documento del DOF válido.")

        inserted = 0
        skipped = 0
        errors = []

        for art_data in parsed_articles:
            try:
                # 2. Generar embedding para cada artículo
                vector = await embedding_engine.generate_embedding(art_data["cuerpo_texto"])

                # 3. Construir entidad y guardar
                article = LegalArticle(
                    materia_juridica=art_data["materia_juridica"],
                    ley_o_codigo=art_data["ley_o_codigo"],
                    libro_o_titulo=art_data.get("libro_o_titulo"),
                    numero_articulo=art_data["numero_articulo"],
                    cuerpo_texto=art_data["cuerpo_texto"],
                    archivo_json_url=archivo_url,
                    embedding=vector
                )

                result = await self.repository.create_article(article)
                if result is None:
                    skipped += 1
                else:
                    inserted += 1

            except Exception as e:
                errors.append(f"{art_data['numero_articulo']}: {str(e)}")
                logger.error(f"Error al procesar {art_data['numero_articulo']}: {e}")

        ley_nombre = parsed_articles[0]["ley_o_codigo"] if parsed_articles else "Desconocida"

        return {
            "ley": ley_nombre,
            "total_extraidos": len(parsed_articles),
            "insertados": inserted,
            "duplicados_omitidos": skipped,
            "errores": errors
        }
