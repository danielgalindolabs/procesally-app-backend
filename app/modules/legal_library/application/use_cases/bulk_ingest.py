import logging
from typing import Dict, Optional

from app.core.config import settings
from app.modules.legal_library.adapters.app_domain_mapper import AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppInputDTO,
    DocumentAppInputDTO,
)
from app.modules.legal_library.domain.entities.legal_document_entity import (
    LegalDocumentEntity,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)
from app.modules.legal_library.domain.services.document_parser import DocumentParser
from app.modules.legal_library.domain.services.embedding_service import EmbeddingService
from app.modules.share.domain.exceptions.dof_exceptions import InvalidDOFDocumentError
from app.modules.share.infrastructure.parsers.dof_parser import (
    _infer_materia_from_keywords,
)

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
        document_metadata: Optional[DocumentAppInputDTO] = None,
        max_articles: Optional[int] = None,
    ) -> Dict:
        # 0. Registrar el documento legal de origen si viene la metadata
        document_id = None
        previous_document_id_to_replace: Optional[int] = None
        if document_metadata:
            # VALIDACIÓN: Evitar duplicados por título en subidas manuales o automáticas
            # Si el documento ya existe con la misma fecha de reforma, no procesamos.
            existing_doc = None
            if document_metadata.url_oficial:
                existing_doc = await self.repository.get_document_by_url(
                    document_metadata.url_oficial
                )

            if existing_doc is None:
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
                        "Actualizando %s: la versión previa se eliminará solo al finalizar ingesta completa.",
                        document_metadata.titulo,
                    )
                    previous_document_id_to_replace = existing_doc.id

            # Inferir materias del nombre de la ley
            document_materias = _infer_materia_from_keywords(
                document_metadata.titulo.lower()
            )

            doc_entity = LegalDocumentEntity(
                titulo=document_metadata.titulo,
                nombre_archivo=document_metadata.nombre_archivo,
                url_oficial=document_metadata.url_oficial,
                url_interna=document_metadata.url_interna,
                fecha_publicacion=document_metadata.fecha_publicacion,
                fecha_ultima_reforma=document_metadata.fecha_ultima_reforma,
                materias_juridicas=document_materias,
            )
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

        selected_articles = self._select_articles_for_sampling(
            parsed_articles, max_articles
        )

        inserted = 0
        errors = []

        for art in selected_articles:
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

                rich_text = f"""
Ley: {art.ley_o_codigo}
Materia: {art.materia_juridica}
Título: {art.libro_o_titulo or "N/A"}
Artículo: {art.numero_articulo}
Publicación: {fecha_pub}
Reforma: {fecha_ref}

Contenido:
{art.cuerpo_texto}
""".strip()

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

        ingest_is_complete = inserted == len(selected_articles) and not errors
        if settings.INGEST_REQUIRE_COMPLETE and not ingest_is_complete:
            await self._cleanup_partial_ingest(document_id, archivo_url)
            raise InvalidDOFDocumentError(
                detail=(
                    "La ingesta no se completó. Se revirtieron datos parciales para "
                    "garantizar consistencia."
                )
            )

        if previous_document_id_to_replace and document_id:
            await self.repository.delete_document(previous_document_id_to_replace)

        ley_nombre = (
            parsed_articles[0].ley_o_codigo if parsed_articles else "Desconocida"
        )

        return {
            "ley": ley_nombre,
            "total_extraidos": len(parsed_articles),
            "total_muestreados": len(selected_articles),
            "insertados": inserted,
            "errores": errors,
        }

    async def _cleanup_partial_ingest(
        self, document_id: Optional[int], archivo_url: str
    ) -> None:
        try:
            if document_id:
                await self.repository.delete_document(document_id)
                return

            await self.repository.delete_articles_by_file(archivo_url)
        except Exception as cleanup_error:
            logger.error(
                "Error al limpiar ingesta parcial para %s: %s",
                archivo_url,
                cleanup_error,
            )

    def _select_articles_for_sampling(
        self, parsed_articles: list, max_articles: Optional[int]
    ):
        if not max_articles or max_articles <= 0:
            return parsed_articles

        total = len(parsed_articles)
        if max_articles >= total:
            return parsed_articles

        if max_articles == 1:
            return [parsed_articles[0]]

        last_index = total - 1
        step_base = max_articles - 1
        selected_indices = []
        seen = set()

        for i in range(max_articles):
            idx = round((i * last_index) / step_base)
            if idx not in seen:
                selected_indices.append(idx)
                seen.add(idx)

        if len(selected_indices) < max_articles:
            for idx in range(total):
                if idx in seen:
                    continue
                selected_indices.append(idx)
                if len(selected_indices) == max_articles:
                    break

        selected_indices.sort()
        return [parsed_articles[idx] for idx in selected_indices]
