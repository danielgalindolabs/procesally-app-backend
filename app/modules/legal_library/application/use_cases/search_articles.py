import re
import logging
from typing import List

from app.modules.legal_library.adapters.app_domain_mapper import AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppOutputDTO,
)
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)
from app.modules.legal_library.domain.services.embedding_service import EmbeddingService
from app.modules.legal_library.domain.services.legal_router_service import (
    LegalRouterService,
)
from app.share.exceptions.base_exceptions import InfrastructureException

logger = logging.getLogger("app.legal_library.use_cases.search_articles")


class SearchArticlesUseCase:
    """Caso de uso orquestador para la búsqueda híbrida (Semántica + Estructurada)."""

    def __init__(
        self,
        repository: LegalRepository,
        embedding_service: EmbeddingService,
        router_service: LegalRouterService,
    ):
        self.repository = repository
        self.embedding_service = embedding_service
        self.router_service = router_service

    def _extract_article_numbers(self, query: str) -> List[str]:
        """Extrae números de artículos usando una regex robusta para producción."""
        # Soporta: "Art. 1", "Artículos 2, 3 y 4", "arts 5 y 6", "art 1,2"
        # Primero buscamos la mención a artículo(s) y luego capturamos los números
        pattern = r"art(?:ículo|s)?\.?\s*(\d+(?:\s*,\s*\d+|\s*y\s*\d+)*)"
        matches = re.findall(pattern, query.lower())

        numbers = []
        for match in matches:
            # Separamos por coma o "y"
            parts = re.split(r",|y", match)
            for p in parts:
                num = p.strip()
                if num.isdigit():
                    numbers.append(f"Art. {num}")

        # Deduplicamos manteniendo el orden original
        seen = set()
        return [x for x in numbers if not (x in seen or seen.add(x))]

    def _determine_intent(self, query: str, numbers: List[str]) -> str:
        """Determina la intención con precisión legal (Senior UX)."""
        if not numbers:
            return "semantic"

        q_lower = query.lower()

        # Palabras clave que sugieren una intención de explicación o relación semántica
        semantic_keywords = [
            "explica",
            "relacion",
            "diferencia",
            "comparar",
            "ejemplo",
            "interpretación",
            "caso",
            "aplica",
            "porque",
            "por que",
            "cómo",
            "como",
            "cuándo",
            "cuando",
        ]

        # Si hay artículos detectados pero NO hay palabras clave semánticas claras,
        # asumimos que el usuario quiere el texto exacto (Ruta Directa).
        has_semantic_intent = any(k in q_lower for k in semantic_keywords)

        if not has_semantic_intent:
            return "direct"

        return "hybrid"

    async def execute(
        self,
        consulta: str,
        limite: int,
        materia_juridica: str | None = None,
        ley_o_codigo: str | None = None,
    ) -> list[ArticleAppOutputDTO]:
        try:
            # 0. Normalización de Ley (Smart Default)
            if not ley_o_codigo:
                ley_o_codigo = "CÓDIGO CIVIL FEDERAL"

            # 1. Extracción de Intención y Números
            extracted_numbers = self._extract_article_numbers(consulta)
            intent = self._determine_intent(consulta, extracted_numbers)

            # Registro estructurado para observabilidad en producción
            logger.info(
                f"Búsqueda Híbrida | Intent: {intent} | Arts: {extracted_numbers} | Query: {consulta}"
            )

            # 2. Router: Detección de materia si no viene explícita
            if not materia_juridica:
                materia_juridica = await self.router_service.detect_materia(consulta)

            entities = []

            # --- RUTA ESTRUCTURADA (SQL Bypass) ---
            sql_results = []
            if extracted_numbers:
                sql_results = await self.repository.get_articles_by_numbers(
                    extracted_numbers, ley_o_codigo
                )

                # Preservar el orden de los artículos solicitado por el usuario (Problem 1 Fix)
                order_map = {num: i for i, num in enumerate(extracted_numbers)}
                sql_results.sort(key=lambda x: order_map.get(x.numero_articulo, 999))

                for res in sql_results:
                    # Score override para garantizar Top 1 sin romper distribución
                    res.similitud = 0.99

            # --- DECISIÓN DE FLUJO ---
            if intent == "direct" and sql_results:
                # Si es búsqueda directa y lo encontramos por SQL, terminamos rápido.
                entities = sql_results
            else:
                # --- RUTA SEMÁNTICA (Vector Search) ---
                query_enriquecida = f"""
Consulta legal: {consulta}
Materia jurídica: {materia_juridica or "No especificada"}
Contexto: Buscar artículos relevantes en {ley_o_codigo} con interpretación jurídica.
""".strip()

                query_vector = await self.embedding_service.generate_embedding(
                    query_enriquecida
                )

                # Recuperación Ampliada (Problem 3) para permitir re-ranking y evitar pérdida de recall
                top_k_vector = limite * 5
                semantic_results = await self.repository.search_similar_vectors(
                    query_vector,
                    top_k_vector,
                    materia_juridica=materia_juridica,
                    ley_o_codigo=ley_o_codigo,
                )

                # --- MERGE INTELIGENTE Y DEDUPLICACIÓN POR CLAVE COMPUESTA ---
                seen_keys = set()
                merged_list = []
                for e in sql_results + semantic_results:
                    # Un artículo es igual a otro si tienen la misma ley y número
                    key = (e.ley_o_codigo.lower(), e.numero_articulo.lower())
                    if key not in seen_keys:
                        seen_keys.add(key)
                        merged_list.append(e)

                entities = merged_list

                # --- RE-RANKING HÍBRIDO ---
                def calculate_boosted_score(entity) -> float:
                    # El match exacto vía SQL manda
                    if entity.similitud == 0.99:
                        return 0.99

                    score = entity.similitud or 0.0
                    content_lower = entity.cuerpo_texto.lower()
                    query_terms = [t for t in consulta.lower().split() if len(t) > 3]

                    # Boost por coincidencia de términos clave
                    for term in query_terms:
                        if term in content_lower:
                            score += 0.04

                    # Fallback de seguridad: si el número está pero SQL no respondió (ej. distinta ley)
                    for n_str in extracted_numbers:
                        if n_str.lower() in entity.numero_articulo.lower():
                            score = max(score, 0.92)

                    entity.similitud = round(score, 4)
                    return score

                entities.sort(key=calculate_boosted_score, reverse=True)

            # 3. Mapear de vuelta a DTOs de Aplicación y Recortar al límite
            final_entities = entities[:limite]
            return [AppDomainMapper.domain_to_app_output(e) for e in final_entities]

        except Exception as e:
            logger.error(f"Error en búsqueda híbrida: {e}")
            if "openai" in str(e).lower():
                raise
            raise InfrastructureException(
                message=f"Error durante la búsqueda semántica: {str(e)}",
                code="SEARCH_ERROR",
            )
