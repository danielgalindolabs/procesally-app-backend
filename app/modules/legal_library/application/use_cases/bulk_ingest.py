import logging

from app.modules.legal_library.adapters.app_domain_mapper import AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppInputDTO,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)
from app.modules.legal_library.domain.services.embedding_service import EmbeddingService
from app.share.domain.exceptions.dof_exceptions import InvalidDOFDocumentError
from app.share.infrastructure.parsers.dof_parser import dof_parser

logger = logging.getLogger("app.legal_library.use_cases.bulk_ingest")


class BulkIngestUseCase:
    """Caso de uso orquestador para ingerir artículos en masa desde un HTML.
    Depende EXCLUSIVAMENTE de contratos de dominio.
    """

    def __init__(
        self, repository: LegalRepository, embedding_service: EmbeddingService
    ):
        self.repository = repository
        self.embedding_service = embedding_service

    async def execute(self, html_content: str, archivo_url: str) -> dict:
        # 1. Parsear el HTML con el parser determinístico (Infraestructura cross-cutting)
        try:
            parsed_articles = dof_parser.parse(html_content)
        except Exception as e:
            logger.error(f"Error crítico en el parser DOF: {e}")
            raise InvalidDOFDocumentError(detail=f"Error al analizar el HTML: {str(e)}")

        if not parsed_articles:
            raise InvalidDOFDocumentError()

        inserted = 0
        skipped = 0
        errors = []

        for art_data in parsed_articles:
            try:
                # 2. Generar embedding para cada artículo a través de Servicio de Dominio
                vector = await self.embedding_service.generate_embedding(
                    art_data["cuerpo_texto"]
                )

                # 3. Construir DTO y Entidad
                app_dto = ArticleAppInputDTO(
                    materia_juridica=art_data["materia_juridica"],
                    ley_o_codigo=art_data["ley_o_codigo"],
                    libro_o_titulo=art_data.get("libro_o_titulo"),
                    numero_articulo=art_data["numero_articulo"],
                    cuerpo_texto=art_data["cuerpo_texto"],
                    archivo_json_url=archivo_url,
                )
                article_entity = AppDomainMapper.app_input_to_domain(app_dto, vector)

                # 4. Lanzar a repositorio de Dominio
                result = await self.repository.create_article(article_entity)

                if result is None:
                    skipped += 1
                else:
                    inserted += 1

            except Exception as e:
                errors.append(f"{art_data['numero_articulo']}: {str(e)}")
                logger.error(f"Error al procesar {art_data['numero_articulo']}: {e}")

        ley_nombre = (
            parsed_articles[0]["ley_o_codigo"] if parsed_articles else "Desconocida"
        )

        return {
            "ley": ley_nombre,
            "total_extraidos": len(parsed_articles),
            "insertados": inserted,
            "duplicados_omitidos": skipped,
            "errores": errors,
        }
