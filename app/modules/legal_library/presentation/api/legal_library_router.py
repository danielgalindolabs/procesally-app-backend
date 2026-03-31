from typing import List, Optional

from charset_normalizer import from_bytes
from fastapi import APIRouter, Depends, File, UploadFile, status

from app.modules.legal_library.adapters.presentation_app_mapper import \
    PresentationAppMapper
from app.modules.legal_library.application.use_cases.bulk_ingest import \
    BulkIngestUseCase
from app.modules.legal_library.application.use_cases.bulk_url_ingest import \
    BulkUrlIngestUseCase
from app.modules.legal_library.application.use_cases.delete_file import \
    DeleteFileUseCase
from app.modules.legal_library.application.use_cases.parse_html_index import \
    ParseHtmlIndexUseCase
from app.modules.legal_library.application.use_cases.search_articles import \
    SearchArticlesUseCase
from app.modules.legal_library.presentation.dependencies.legal_deps import (
    get_bulk_ingest_use_case, get_bulk_url_ingest_use_case,
    get_delete_file_use_case, get_parse_html_index_use_case,
    get_search_articles_use_case)
from app.modules.legal_library.presentation.schemas.article_schemas import (
    BulkUrlIngestRequest, SearchRequest, SearchResult)

router = APIRouter()


@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_dof_file(
    file: UploadFile = File(...),
    titulo: str = "Documento Legal",
    url_oficial: str = "https://www.dof.gob.mx/",
    fecha_publicacion: Optional[str] = None,
    fecha_ultima_reforma: Optional[str] = None,
    bulk_uc: BulkIngestUseCase = Depends(get_bulk_ingest_use_case),
):
    """
    Sube un archivo HTML del DOF y procesa todos sus artículos automáticamente.
    - Crea un registro en 'legal_documents' para seguimiento.
    - Extrae el nombre de la ley, libros, títulos y artículos.
    - Genera embeddings y almacena masivamente vinculando al documento.
    """
    content = await file.read()
    # Usamos charset-normalizer para decodificar archivos subidos (ej. DOF o local)
    decoded = from_bytes(content).best()
    html_str = str(decoded) if decoded else content.decode("utf-8", errors="replace")

    # Mapeo de metadata para el documento de origen
    doc_metadata = PresentationAppMapper.to_document_app_input(
        titulo=titulo,
        nombre_archivo=file.filename or "archivo_desconocido",
        url_oficial=url_oficial,
        fecha_publicacion=fecha_publicacion,
        fecha_ultima_reforma=fecha_ultima_reforma,
    )

    # El archivo_url para el campo antiguo se mantiene como fallback
    return await bulk_uc.execute(
        html_str, archivo_url=file.filename or "", document_metadata=doc_metadata
    )


@router.post("/bulk-url", status_code=status.HTTP_200_OK)
async def bulk_upload_by_url(
    request: BulkUrlIngestRequest,
    bulk_url_uc: BulkUrlIngestUseCase = Depends(get_bulk_url_ingest_use_case),
):
    """
    Ingesta masiva de documentos legales a partir de un diccionario de URLs.
    Cada URL debe pertenecer a un dominio permitido en la configuración.
    """
    app_input = PresentationAppMapper.to_bulk_url_input(request.urls)
    return await bulk_url_uc.execute(app_input)


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


@router.post("/parse-index-html", response_model=dict, status_code=status.HTTP_200_OK)
async def parse_html_index(
    file: UploadFile = File(...),
    parse_uc: ParseHtmlIndexUseCase = Depends(get_parse_html_index_use_case),
):
    """
    Recibe un archivo HTML (ej. la tabla de leyes federales en ordenjuridico) y lo convierte
    en un Diccionario JSON estructurado con títulos, URLs e información de fechas.
    """
    content = await file.read()
    # Decodificación robusta usando charset-normalizer
    decoded = from_bytes(content).best()
    html_str = str(decoded) if decoded else content.decode("utf-8", errors="replace")

    # Usamos execute pasándole el contenido HTML directamente
    result = parse_uc.execute(html_content=html_str)

    return result
