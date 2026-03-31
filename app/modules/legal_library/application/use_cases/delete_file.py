import logging

from app.modules.legal_library.application.schemas.article_app_schemas import \
    DeleteFileAppInputDTO
from app.modules.legal_library.domain.repositories.legal_repository import \
    LegalRepository

logger = logging.getLogger("app.legal_library.use_cases.delete_file")


class DeleteFileUseCase:
    """Caso de uso para eliminar todos los artículos de un archivo específico."""

    def __init__(self, repository: LegalRepository):
        self.repository = repository

    async def execute(self, input_dto: DeleteFileAppInputDTO) -> dict:
        """Ejecuta la eliminación completa del documento y sus artículos."""
        filename = input_dto.archivo_json_url
        logger.info(f"Iniciando eliminación total para el archivo: {filename}")

        # 1. Buscar el documento por nombre de archivo
        existing_doc = await self.repository.get_document_by_filename(filename)

        if not existing_doc:
            # Fallback: intentar borrar solo artículos si el documento no existe (legacy)
            logger.warning(
                f"No se encontró record de documento para {filename}. "
                "Intentando borrar artículos huérfanos."
            )
            count = await self.repository.delete_articles_by_file(filename)
            return {
                "archivo": filename,
                "documento_eliminado": False,
                "articulos_eliminados": count,
                "status": "partial_success_orphans" if count > 0 else "not_found",
            }

        # 2. Borrado total (Documento + Artículos asociados por document_id)
        doc_id = existing_doc.id
        await self.repository.delete_document(doc_id)  # type: ignore

        logger.info(
            f"Eliminación completa de {filename} (ID: {doc_id}) realizada con éxito."
        )

        return {
            "archivo": filename,
            "documento_id": doc_id,
            "documento_eliminado": True,
            "status": "success",
        }
