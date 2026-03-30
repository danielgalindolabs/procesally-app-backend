from typing import List

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.modules.legal_library.adapters.presentation_app_mapper import (
    PresentationAppMapper,
)
from app.modules.legal_library.application.use_cases.bulk_ingest import (
    BulkIngestUseCase,
)
from app.modules.legal_library.application.use_cases.create_article import (
    CreateArticleUseCase,
)
from app.modules.legal_library.application.use_cases.delete_file import (
    DeleteFileUseCase,
)
from app.modules.legal_library.application.use_cases.search_articles import (
    SearchArticlesUseCase,
)
from app.modules.legal_library.presentation.dependencies.legal_deps import (
    get_bulk_ingest_use_case,
    get_create_article_use_case,
    get_delete_file_use_case,
    get_search_articles_use_case,
)
from app.modules.legal_library.presentation.schemas.article_schemas import (
    ArticleCreateRequest,
    ArticleResponse,
    SearchRequest,
    SearchResult,
)

router = APIRouter()


@router.post("/", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def upload_article(
    request: ArticleCreateRequest,
    create_uc: CreateArticleUseCase = Depends(get_create_article_use_case),
):
    """
    Ingesta un nuevo artículo legal en la biblioteca manual.
    """
    # 1. Mapea el Request HTTP a un DTO de Aplicación
    app_input = PresentationAppMapper.to_app_input(request)

    # 2. Ejecuta caso de uso
    app_output = await create_uc.execute(app_input)

    # FastAPI casteará automáticamente el AppOutputDTO a ArticleResponse gracias a response_model
    return app_output


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_dof_file(
    file: UploadFile = File(...),
    bulk_uc: BulkIngestUseCase = Depends(get_bulk_ingest_use_case),
):
    """
    Sube un archivo HTML del DOF y procesa todos sus artículos automáticamente.
    - Extrae el nombre de la ley, libros, títulos y artículos.
    - Genera embeddings para cada artículo.
    - Almacena masivamente en la base de datos vectorial.
    """
    content = await file.read()
    # Asumimos que el DOF usa UTF-8 o ISO-8859-1 (latin-1) usualmente.
    try:
        html_str = content.decode("utf-8")
    except UnicodeDecodeError:
        html_str = content.decode("latin-1")

    # El archivo_url en este caso es el nombre del archivo original
    return await bulk_uc.execute(html_str, archivo_url=file.filename)


@router.post("/search", response_model=List[SearchResult])
async def search_articles(
    request: SearchRequest,
    search_uc: SearchArticlesUseCase = Depends(get_search_articles_use_case),
):
    """
    Búsqueda semántica en la biblioteca legal.
    - Convierte la consulta en lenguaje natural a un vector
    - Busca los artículos más similares usando distancia coseno (pgvector)
    - Retorna los resultados ordenados por relevancia
    """
    # Pasamos las primitivas y filtros para no acoplar el Caso de Uso a esquemas de Presentación
    results = await search_uc.execute(
        consulta=request.consulta,
        limite=request.limite,
        materia_juridica=request.materia_juridica,
        ley_o_codigo=request.ley_o_codigo,
    )

    # FastAPI casteará de List[ArticleAppOutputDTO] -> List[SearchResult]
    return results


@router.delete("/files/{file_name}", status_code=status.HTTP_200_OK)
async def delete_legal_file(
    file_name: str,
    delete_uc: DeleteFileUseCase = Depends(get_delete_file_use_case),
):
    """
    Elimina todos los artículos asociados a un nombre de archivo específico.
    """
    # Mapeo a DTO de Aplicación
    app_input = PresentationAppMapper.to_delete_file_input(file_name)

    # Ejecución
    return await delete_uc.execute(app_input)
