import pytest

from app.core.config import settings
from app.modules.legal_library.infrastructure.services.legal_router_service_impl import (
    LegalRouterServiceImpl,
)
from app.modules.share.infrastructure.services.embedding_service import engine


@pytest.mark.asyncio
async def test_zero_embeddings_enabled_for_parsing_phase():
    vector = await engine.generate_embedding("texto de prueba legal")

    assert settings.PARSING_ONLY_MODE is True
    assert settings.USE_ZERO_EMBEDDINGS is True
    assert len(vector) == settings.ZERO_EMBEDDING_DIM
    assert set(vector) == {0.0}


@pytest.mark.asyncio
async def test_legal_router_skips_llm_when_disabled():
    class ExplosiveClient:
        @property
        def chat(self):
            raise AssertionError("No debe invocarse OpenAI en parsing-only")

    old_client = engine.client
    engine.client = ExplosiveClient()

    try:
        router = LegalRouterServiceImpl()

        # Heurística local sigue activa
        detected = await router.detect_materia("calcular impuesto sobre la renta")
        assert detected == "Fiscal"

        # Sin heurística y con LLM desactivado, retorna None sin tocar cliente
        unknown = await router.detect_materia("consulta neutra sin palabras clave")
        assert unknown is None
    finally:
        engine.client = old_client
