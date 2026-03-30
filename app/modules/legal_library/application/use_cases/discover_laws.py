import logging

from app.modules.legal_library.application.schemas.article_app_schemas import (
    DiscoverLawsAppInputDTO,
    DiscoverLawsAppOutputDTO,
)
from app.modules.legal_library.domain.services.document_downloader import (
    DocumentDownloader,
)
from app.modules.legal_library.domain.services.legal_indexer import LegalIndexer

logger = logging.getLogger("app.legal_library.use_cases.discover_laws")


class DiscoverLawsUseCase:
    """Caso de uso para descubrir (scrapear) enlaces a leyes desde una página índice."""

    def __init__(
        self,
        indexer: LegalIndexer,
        downloader: DocumentDownloader,
    ):
        self.indexer = indexer
        self.downloader = downloader

    async def execute(
        self, input_dto: DiscoverLawsAppInputDTO
    ) -> DiscoverLawsAppOutputDTO:
        url = input_dto.index_url

        try:
            logger.info(f"Iniciando descubrimiento de leyes en el índice: {url}")
            # 1. Descargamos el HTML de la página índice
            html_content = await self.downloader.fetch_content(url)

            # 2. Inyectamos a nuestro LegalIndexer para que extraiga los enlaces
            discovered_urls = self.indexer.discover_links(
                html_content=html_content, base_url=url
            )

            return DiscoverLawsAppOutputDTO(
                total_found=len(discovered_urls),
                urls=discovered_urls,
            )

        except Exception as e:
            logger.error(f"Fallo al descubrir leyes en {url}: {e}")
            raise
