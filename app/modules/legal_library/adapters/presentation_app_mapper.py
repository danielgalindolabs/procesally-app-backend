from typing import Optional

from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppInputDTO,
    BulkUrlIngestAppInputDTO,
    DeleteFileAppInputDTO,
    DocumentAppInputDTO,
)
from app.modules.legal_library.presentation.schemas.article_schemas import (
    ArticleCreateRequest,
)


class PresentationAppMapper:
    @staticmethod
    def to_app_input(request: ArticleCreateRequest) -> ArticleAppInputDTO:
        # Aquí mapeamos de Pydantic Schema a Dataclass DTO
        return ArticleAppInputDTO(
            materia_juridica=request.materia_juridica,
            ley_o_codigo=request.ley_o_codigo,
            numero_articulo=request.numero_articulo,
            cuerpo_texto=request.cuerpo_texto,
            archivo_json_url=str(request.archivo_json_url),
            libro_o_titulo=request.libro_o_titulo,
        )

    @staticmethod
    def to_document_app_input(
        titulo: str,
        nombre_archivo: str,
        url_oficial: str,
        url_interna: Optional[str] = None,
    ) -> DocumentAppInputDTO:
        return DocumentAppInputDTO(
            titulo=titulo,
            nombre_archivo=nombre_archivo,
            url_oficial=url_oficial,
            url_interna=url_interna,
        )

    @staticmethod
    def to_delete_file_input(file_url: str) -> DeleteFileAppInputDTO:
        return DeleteFileAppInputDTO(archivo_json_url=file_url)

    @staticmethod
    def to_bulk_url_input(urls: dict) -> BulkUrlIngestAppInputDTO:
        # urls es un dict de { str: DocumentMetadataInfo }
        # Convertimos a { str: { "url": str, "fecha_pub": str, "fecha_ref": str } }
        clean_data = {}
        for titulo, info in urls.items():
            clean_data[titulo] = {
                "url": str(info.id),
                "fecha_pub": info.fecha_de_publicacion,
                "fecha_ref": info.fecha_de_ultima_reforma,
            }
        return BulkUrlIngestAppInputDTO(urls=clean_data)


    # Nota: El regreso desde AppOutputDTO a ArticleResponse (Presentation)
    # se suele resolver fácilmente si los campos coinciden porque Pydantic model_validate
    # o dict() hacen matching. Sin embargo, puede ser explícito en el router.
