import logging

from app.modules.legal_library.adapters.app_domain_mapper import AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppInputDTO,
    DocumentAppInputDTO,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)
from app.modules.legal_library.domain.services.document_parser import DocumentParser
from app.modules.legal_library.domain.services.embedding_service import EmbeddingService
from app.share.domain.exceptions.dof_exceptions import InvalidDOFDocumentError

logger = logging.getLogger("app.legal_library.use_cases.bulk_ingest")


class BulkIngestUseCase:
    """Caso de uso orquestador para ingerir artículos en masa desde un documento.
    Depende EXCLUSIVAMENTE de contratos de dominio.
    """

    def __init__(
        self,
        repository: LegalRepository,
        embedding_service: EmbeddingService,
        document_parser: DocumentParser,
    ):
        self.repository = repository
        self.embedding_service = embedding_service
        self.document_parser = document_parser

    async def execute(
        self,
        content: str,
        archivo_url: str,
        document_metadata: DocumentAppInputDTO | None = None,
    ) -> dict:
        # 0. Registrar el documento legal de origen si viene la metadata
        document_id = None
        if document_metadata:
            # VALIDACIÓN: Evitar duplicados por título en subidas manuales o automáticas
            # Si el documento ya existe con la misma fecha de reforma, no procesamos.
            existing_doc = await self.repository.get_document_by_title(
                document_metadata.titulo
            )

            if existing_doc:
                if (
                    existing_doc.fecha_ultima_reforma
                    == document_metadata.fecha_ultima_reforma
                ):
                    logger.info(
                        f"Omitiendo {document_metadata.titulo}: Ya existe con la misma fecha de reforma."
                    )
                    return {
                        "ley": document_metadata.titulo,
                        "status": "skipped",
                        "total_extraidos": 0,
                        "insertados": 0,
                        "motivo": "Versión idéntica ya presente en la biblioteca.",
                    }
                else:
                    logger.warning(
                        f"Actualizando {document_metadata.titulo}: Borrando artículos previos."
                    )
                    await self.repository.delete_document(existing_doc.id)  # type: ignore

            doc_entity = AppDomainMapper.document_app_to_domain(document_metadata)
            saved_doc = await self.repository.create_document(doc_entity)
            document_id = saved_doc.id

        # 1. Parsear el contenido con el parser inyectado (puede ser HTML, PDF, XML, etc.)
        try:
            parsed_articles = self.document_parser.parse(content)
        except Exception as e:
            logger.error(f"Error crítico en el parser: {e}")
            raise InvalidDOFDocumentError(
                detail=f"Error al analizar el documento: {str(e)}"
            )

        if not parsed_articles:
            raise InvalidDOFDocumentError()

        inserted = 0
        errors = []

        for art in parsed_articles:
            try:
                # 2. Enriquecer el texto con metadata para el embedding
                fecha_pub = (
                    document_metadata.fecha_publicacion if document_metadata else "N/A"
                )
                fecha_ref = (
                    document_metadata.fecha_ultima_reforma
                    if document_metadata
                    else "N/A"
                )

                rich_text = (
                    f"Materia: {art.materia_juridica}. "
                    f"Ley: {art.ley_o_codigo}. "
                    f"Art: {art.numero_articulo}. "
                    f"Publicación: {fecha_pub}. "
                    f"Reforma: {fecha_ref}. "
                    f"Contenido: {art.cuerpo_texto}"
                )

                # Generar embedding a través de Servicio de Dominio
                vector = await self.embedding_service.generate_embedding(rich_text)

                # 3. Construir DTO y Entidad
                app_dto = ArticleAppInputDTO(
                    materia_juridica=art.materia_juridica,
                    ley_o_codigo=art.ley_o_codigo,
                    libro_o_titulo=art.libro_o_titulo,
                    numero_articulo=art.numero_articulo,
                    cuerpo_texto=art.cuerpo_texto,
                    archivo_json_url=archivo_url,
                    document_id=document_id,
                )
                article_entity = AppDomainMapper.app_input_to_domain(app_dto, vector)

                # 4. Lanzar a repositorio de Dominio
                await self.repository.create_article(article_entity)
                inserted += 1

            except Exception as e:
                errors.append(f"{art.numero_articulo}: {str(e)}")
                logger.error(f"Error al procesar {art.numero_articulo}: {e}")

        ley_nombre = (
            parsed_articles[0].ley_o_codigo if parsed_articles else "Desconocida"
        )

        return {
            "ley": ley_nombre,
            "total_extraidos": len(parsed_articles),
            "insertados": inserted,
            "errores": errors,
        }
