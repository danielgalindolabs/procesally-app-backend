import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.legal_library.application.schemas.article_app_schemas import (
    BulkUrlIngestAppInputDTO,
    BulkUrlSampleOptionsAppInputDTO,
)
from app.modules.legal_library.application.use_cases.bulk_url_ingest_dev_sample import (
    BulkUrlIngestDevSampleUseCase,
)
from app.modules.legal_library.presentation.dependencies.legal_deps import (
    get_bulk_url_ingest_dev_sample_use_case,
)


class _FakeDownloader:
    def __init__(self, size_map: dict[str, int]):
        self.size_map = size_map

    async def fetch_content(self, url: str) -> str:
        return f"<html><body><p>Contenido para {url}</p></body></html>"

    async def head_content_length(self, url: str):
        return self.size_map.get(url)


class _FakeBulkIngest:
    def __init__(self):
        self.calls = []

    async def execute(
        self, content: str, archivo_url: str, document_metadata=None, max_articles=None
    ):
        inserted = int(max_articles or 0)
        self.calls.append({"url": archivo_url, "max_articles": inserted})
        return {
            "ley": document_metadata.titulo if document_metadata else "N/A",
            "total_extraidos": inserted,
            "total_muestreados": inserted,
            "insertados": inserted,
            "errores": [],
        }


@pytest.mark.asyncio
async def test_dev_sample_use_case_reaches_target_articles():
    fake_bulk = _FakeBulkIngest()
    fake_downloader = _FakeDownloader(
        {
            "https://www.ordenjuridico.gob.mx/a.html": 900,
            "https://www.ordenjuridico.gob.mx/b.html": 700,
            "https://www.ordenjuridico.gob.mx/c.html": 500,
        }
    )
    use_case = BulkUrlIngestDevSampleUseCase(fake_bulk, fake_downloader)

    input_dto = BulkUrlIngestAppInputDTO(
        urls={
            "Ley Civil de Prueba": {
                "url": "https://www.ordenjuridico.gob.mx/a.html",
                "fecha_pub": "01-01-2020",
                "fecha_ref": "01-01-2024",
            },
            "Ley Mercantil de Prueba": {
                "url": "https://www.ordenjuridico.gob.mx/b.html",
                "fecha_pub": "01-01-2020",
                "fecha_ref": "01-01-2024",
            },
            "Ley Penal de Prueba": {
                "url": "https://www.ordenjuridico.gob.mx/c.html",
                "fecha_pub": "01-01-2020",
                "fecha_ref": "01-01-2024",
            },
        }
    )
    options = BulkUrlSampleOptionsAppInputDTO(
        target_articulos=250,
        max_articulos_por_ley=100,
        max_leyes=10,
        modo="hybrid",
        dry_run=False,
        seed=7,
    )

    result = await use_case.execute(input_dto, options)

    assert result["resumen_general"]["insertados"] == 250
    assert result["resumen_general"]["leyes_procesadas"] == 3
    assert len(fake_bulk.calls) == 3
    assert fake_bulk.calls[-1]["max_articles"] == 50


def test_dev_sample_endpoint_accepts_same_bulk_input(client: TestClient):
    class _FakeDevSampleUC:
        async def execute(self, input_dto, options):
            return {
                "ok": True,
                "urls": len(input_dto.urls),
                "target": options.target_articulos,
                "max_articulos_por_ley": options.max_articulos_por_ley,
            }

    app.dependency_overrides[get_bulk_url_ingest_dev_sample_use_case] = lambda: (
        _FakeDevSampleUC()
    )

    try:
        payload = {
            "urls": {
                "Ley de Prueba": {
                    "id": "https://www.ordenjuridico.gob.mx/test.html",
                    "fecha_de_publicacion": "01-01-2020",
                    "fecha_de_ultima_reforma": "01-01-2024",
                }
            }
        }
        response = client.post(
            "/api/v1/legal/bulk-url/dev-sample?target_articulos=10000&max_articulos_por_ley=120",
            json=payload,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["urls"] == 1
        assert data["target"] == 10000
        assert data["max_articulos_por_ley"] == 120
    finally:
        app.dependency_overrides.pop(get_bulk_url_ingest_dev_sample_use_case, None)
