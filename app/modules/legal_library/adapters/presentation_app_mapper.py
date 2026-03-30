from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppInputDTO,
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

    # Nota: El regreso desde AppOutputDTO a ArticleResponse (Presentation)
    # se suele resolver fácilmente si los campos coinciden porque Pydantic model_validate
    # o dict() hacen matching. Sin embargo, puede ser explícito en el router.
