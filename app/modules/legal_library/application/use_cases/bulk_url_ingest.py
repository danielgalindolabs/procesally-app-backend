import logging

from app.modules.legal_library.application.schemas.article_app_schemas import (
    BulkUrlIngestAppInputDTO, DocumentAppInputDTO)
from app.modules.legal_library.application.use_cases.bulk_ingest import \
    BulkIngestUseCase
from app.modules.legal_library.domain.services.document_downloader import \
    DocumentDownloader

logger = logging.getLogger("app.legal_library.use_cases.bulk_url_ingest")


class BulkUrlIngestUseCase:
    """Caso de uso para ingerir documentos legales masivamente desde URLs."""

    def __init__(
        self,
        bulk_ingest_uc: BulkIngestUseCase,
        document_downloader: DocumentDownloader,
    ):
        self.bulk_ingest_uc = bulk_ingest_uc
        self.document_downloader = document_downloader

    async def execute(self, input_dto: BulkUrlIngestAppInputDTO) -> dict:
        results = {}
        total_success = 0
        total_errors = 0

        for titulo, info in input_dto.urls.items():
            try:
                # info es un dict: { "url": str, "fecha_pub": str, "fecha_ref": str }
                url = info["url"]
                fecha_pub = info.get("fecha_pub")
                fecha_ref = info.get("fecha_ref")

                # VALIDACIÓN: ¿Ya existe? ¿Ha cambiado? Evitamos descarga si está al día.
                existing_doc = await self.bulk_ingest_uc.repository.get_document_by_url(
                    url
                )

                if existing_doc:
                    if existing_doc.fecha_ultima_reforma == fecha_ref:
                        logger.info(
                            f"Omitiendo descarga de {titulo}: Ya está al día (reforma: {fecha_ref})"
                        )
                        results[titulo] = {
                            "status": "skipped",
                            "motivo": "Documento ya existe y no tiene cambios en su metadata.",
                        }
                        continue
                    else:
                        logger.warning(
                            f"Detectado cambio en {titulo}. Borrando versión anterior para actualizar."
                        )
                        await self.bulk_ingest_uc.repository.delete_document(
                            existing_doc.id  # type: ignore
                        )

                logger.info(f"Procesando descarga para: {titulo} desde {url}")

                # 1. Descargar contenido a través de la abstracción
                content = await self.document_downloader.fetch_content(url)

                # 2. Preparar metadata del documento
                doc_metadata = DocumentAppInputDTO(
                    titulo=titulo,
                    nombre_archivo=url.split("/")[-1] or f"{titulo}.html",
                    url_oficial=url,
                    url_interna=None,
                    fecha_publicacion=fecha_pub,
                    fecha_ultima_reforma=fecha_ref,
                )

                # 3. Delegar al BulkIngestUseCase existente para parsear e insertar
                # Usamos el nombre del archivo como identificador
                res = await self.bulk_ingest_uc.execute(
                    content=content,
                    archivo_url=url,
                    document_metadata=doc_metadata,
                )
                results[titulo] = res
                total_success += 1

            except Exception as e:
                logger.error(f"Error procesando URL para {titulo}: {e}")
                results[titulo] = {"error": str(e)}
                total_errors += 1

        return {
            "resumen_general": {
                "total_procesados": len(input_dto.urls),
                "exitosos": total_success,
                "fallidos": total_errors,
            },
            "detalles": results,
        }
