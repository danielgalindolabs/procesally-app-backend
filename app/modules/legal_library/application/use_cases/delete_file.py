import logging

from app.modules.legal_library.application.schemas.article_app_schemas import (
    DeleteFileAppInputDTO,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)

logger = logging.getLogger("app.legal_library.use_cases.delete_file")


class DeleteFileUseCase:
    """Caso de uso para eliminar todos los artículos de un archivo específico."""

    def __init__(self, repository: LegalRepository):
        self.repository = repository

    async def execute(self, input_dto: DeleteFileAppInputDTO) -> dict:
        """Ejecuta la eliminación y retorna el resultado."""
        logger.info(
            f"Iniciando eliminación de artículos para el archivo: {input_dto.archivo_json_url}"
        )

        count = await self.repository.delete_articles_by_file(
            input_dto.archivo_json_url
        )

        logger.info(f"Eliminación completada. {count} artículos eliminados.")

        return {
            "archivo": input_dto.archivo_json_url,
            "articulos_eliminados": count,
            "status": "success" if count > 0 else "no_articles_found",
        }
