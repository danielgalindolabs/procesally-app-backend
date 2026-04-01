import logging
import re
from typing import List, Optional, Tuple

from app.core.legal_config import LAW_MAPPINGS, NUMBER_WORDS, SEMANTIC_KEYWORDS
from app.modules.legal_library.adapters.app_domain_mapper import AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import (
    ArticleAppOutputDTO,
)
from app.modules.legal_library.domain.entities.article_entity import ArticleEntity
from app.modules.legal_library.domain.repositories.legal_repository import (
    LegalRepository,
)
from app.modules.legal_library.domain.services.embedding_service import EmbeddingService
from app.modules.legal_library.domain.services.legal_router_service import (
    LegalRouterService,
)
from app.share.exceptions.base_exceptions import InfrastructureException

logger = logging.getLogger("app.legal_library.use_cases.search_articles")

Intent = str


class SearchArticlesUseCase:
    def __init__(
        self,
        repository: LegalRepository,
        embedding_service: EmbeddingService,
        router_service: LegalRouterService,
    ):
        self.repository = repository
        self.embedding_service = embedding_service
        self.router_service = router_service

    def _extract_articles_from_query(self, query: str) -> Tuple[List[str], bool]:
        """Extrae números de artículos y detecta si hay palabras clave semánticas."""
        q_norm = (
            query.lower()
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
        )

        for word, num in NUMBER_WORDS.items():
            q_norm = re.sub(rf"(articulo\s+){word}\b", rf"\g<1>{num}", q_norm)

        pattern = r"(?:art(?:iculo)?s?\.?)\s*(\d+(?:\s*,\s*\d+|\s*y\s*\d+|\s*e\s*\d+)*)"
        matches = re.findall(pattern, q_norm)

        numbers = []
        for match in matches:
            parts = re.split(r",|y|e", match)
            for p in parts:
                num = p.strip()
                if num.isdigit():
                    numbers.append(f"Art. {num}")

        seen = set()
        unique_numbers = [x for x in numbers if not (x in seen or seen.add(x))]

        has_semantic_context = any(k in query.lower() for k in SEMANTIC_KEYWORDS)

        return unique_numbers, has_semantic_context

    def _extract_law_name(self, query: str) -> Optional[str]:
        """Infiere el nombre de la ley/código mencionado en la consulta."""
        q_norm = (
            query.upper()
            .replace("Á", "A")
            .replace("É", "E")
            .replace("Í", "I")
            .replace("Ó", "O")
            .replace("Ú", "U")
        )

        sorted_keys = sorted(LAW_MAPPINGS.keys(), key=len, reverse=True)

        for term in sorted_keys:
            if re.search(rf"\b{term}\b", q_norm):
                return LAW_MAPPINGS[term]

        return None

    def _determine_intent(
        self, numbers: List[str], has_semantic_context: bool
    ) -> Intent:
        """Determina la intención de búsqueda."""
        if not numbers:
            return "semantic"

        if has_semantic_context:
            return "hybrid"

        return "direct"

    def _deduplicate_articles(
        self,
        articles: List[ArticleEntity],
        preferred_ley: Optional[str] = None,
    ) -> List[ArticleEntity]:
        """Deduplica artículos, prefiriendo el de mayor contenido (norma real vs referencia)."""
        seen_keys = {}
        for article in articles:
            ley_key = (
                article.ley_o_codigo.lower().strip() if article.ley_o_codigo else ""
            )
            numero_key = article.numero_articulo.lower().strip()
            key = (ley_key, numero_key)
            content_length = len(article.cuerpo_texto)
            is_reference = self._is_article_reference(article.cuerpo_texto)

            if key not in seen_keys:
                seen_keys[key] = (article, content_length, is_reference)
            else:
                existing_article, existing_length, existing_is_ref = seen_keys[key]
                if is_reference and not existing_is_ref:
                    continue
                if preferred_ley:
                    existing_match = (
                        existing_article.ley_o_codigo
                        and existing_article.ley_o_codigo.lower().strip()
                        == preferred_ley.lower().strip()
                    )
                    current_match = ley_key == preferred_ley.lower().strip()
                    if existing_match and not current_match:
                        continue
                    if current_match and not existing_match:
                        seen_keys[key] = (article, content_length, is_reference)
                        continue
                if content_length > existing_length:
                    seen_keys[key] = (article, content_length, is_reference)

        return [article for article, _, _ in seen_keys.values()]

    def _is_article_reference(self, cuerpo_texto: str) -> bool:
        """Detecta si el texto es una referencia a otro artículo (no la norma real)."""
        text_lower = cuerpo_texto.lower().strip()
        if len(text_lower) < 150:
            return True
        reference_patterns = [
            r"^(?:iv+|v+|i+)\.",
            r"^art[íi]culo\s+\d+",
            r"^fracci[oó]n",
            r"^inciso",
            r"los\s+art[íi]culos?\s+\d+",
            r"conforme\s+al\s+art[íi]culo",
            r"segun\s+el\s+art[íi]culo",
            r"previstos?\s+en\s+el\s+art[íi]culo",
            r"se\s+regir[áa]\s+por\s+el\s+art[íi]culo",
            r"lo\s+dispuesto\s+en\s+el\s+art[íi]culo",
        ]
        for pattern in reference_patterns:
            if re.match(pattern, text_lower) or re.search(pattern, text_lower[:150]):
                return True
        return False

    def _apply_score_override(
        self, articles: List[ArticleEntity], extracted_numbers: List[str]
    ) -> List[ArticleEntity]:
        """Aplica override de score 0.99 a artículos exactos."""
        normalized_requested = {
            re.sub(r"[^0-9]", "", n.lower()).lstrip("0"): n.lower()
            for n in extracted_numbers
        }

        for article in articles:
            article_num = re.sub(r"[^0-9]", "", article.numero_articulo.lower()).lstrip(
                "0"
            )
            if article_num in normalized_requested:
                article.similitud = 0.99

        return articles

    async def execute(
        self,
        consulta: str,
        limite: Optional[int] = None,
        materia_juridica: Optional[str] = None,
        ley_o_codigo: Optional[str] = None,
    ) -> List[ArticleAppOutputDTO]:
        try:
            extracted_numbers, has_semantic_context = self._extract_articles_from_query(
                consulta
            )
            intent = self._determine_intent(extracted_numbers, has_semantic_context)

            inferred_law = self._extract_law_name(consulta)
            if not ley_o_codigo and inferred_law:
                ley_o_codigo = inferred_law

            if not ley_o_codigo and intent != "semantic":
                ley_o_codigo = "CÓDIGO CIVIL FEDERAL"

            if not materia_juridica:
                materia_juridica = await self.router_service.detect_materia(consulta)

            if inferred_law:
                logger.info(
                    f"Omitiendo filtro de materia por detección de ley: {inferred_law}"
                )
                materia_juridica = None

            logger.info(
                f"Búsqueda | Intent: {intent} | Articles: {extracted_numbers} | Query: {consulta}"
            )

            entities = []

            if intent == "direct":
                entities = await self._handle_direct_intent(
                    extracted_numbers, ley_o_codigo, limite
                )
            elif intent == "hybrid":
                entities = await self._handle_hybrid_intent(
                    consulta,
                    extracted_numbers,
                    ley_o_codigo,
                    materia_juridica,
                    limite,
                )
            else:
                logger.info(
                    f"Llamando _handle_semantic_intent con materia={materia_juridica}, ley={ley_o_codigo}"
                )
                entities = await self._handle_semantic_intent(
                    consulta, materia_juridica, ley_o_codigo, limite
                )
                logger.info(
                    f"_handle_semantic_intent devolvió {len(entities)} resultados"
                )

            return [AppDomainMapper.domain_to_app_output(e) for e in entities]

        except Exception as e:
            logger.error(
                f"Error crítico en HybridSearch | Query: '{consulta}' | Error: {str(e)}",
                exc_info=True,
            )
            if "openai" in str(e).lower() or "asyncpg" in str(e).lower():
                raise
            raise InfrastructureException(
                message=f"Error durante el procesamiento de la búsqueda legal: {str(e)}",
                code="HYBRID_SEARCH_FAILURE",
            )

    async def _handle_direct_intent(
        self,
        extracted_numbers: List[str],
        ley_o_codigo: Optional[str],
        limite: Optional[int],
    ) -> List[ArticleEntity]:
        """Handle DIRECT intent: SQL matches, fallback to semantic if empty."""
        if not extracted_numbers:
            return []

        sql_results = []
        if ley_o_codigo:
            sql_results = await self.repository.get_articles_by_numbers(
                extracted_numbers, ley_o_codigo
            )
            sql_results = self._deduplicate_articles(
                sql_results, preferred_ley=ley_o_codigo
            )
            sql_results = self._apply_score_override(sql_results, extracted_numbers)

        if not sql_results:
            return await self._handle_semantic_fallback(
                extracted_numbers, ley_o_codigo, limite
            )

        def normalize_num(s: str) -> str:
            return re.sub(r"[^0-9]", "", s).lstrip("0")

        order_map = {normalize_num(n): i for i, n in enumerate(extracted_numbers)}
        sql_results.sort(
            key=lambda x: (
                order_map.get(normalize_num(x.numero_articulo), 999),
                -len(x.cuerpo_texto),
            )
        )

        requested_count = len(extracted_numbers)
        final_limit = limite or requested_count
        return sql_results[:final_limit]

    async def _handle_semantic_fallback(
        self,
        extracted_numbers: List[str],
        ley_o_codigo: Optional[str],
        limite: Optional[int],
    ) -> List[ArticleEntity]:
        """Fallback to semantic search when direct SQL finds nothing."""
        query_terms = " ".join(extracted_numbers)
        query = f"Artículo {query_terms}"
        if ley_o_codigo:
            query = f"{ley_o_codigo} {query}"

        query_vector = await self.embedding_service.generate_embedding(query)

        top_k = limite or len(extracted_numbers)
        results = await self.repository.search_similar_vectors(
            query_vector, top_k, ley_o_codigo=ley_o_codigo
        )

        results = self._apply_score_override(results, extracted_numbers)
        results.sort(
            key=lambda x: (x.similitud or 0, -len(x.cuerpo_texto)), reverse=True
        )
        return results

    async def _handle_hybrid_intent(
        self,
        consulta: str,
        extracted_numbers: List[str],
        ley_o_codigo: Optional[str],
        materia_juridica: Optional[str],
        limite: Optional[int],
    ) -> List[ArticleEntity]:
        """Handle HYBRID intent: Exact matches + semantic results."""
        sql_results = []
        if extracted_numbers and ley_o_codigo:
            sql_results = await self.repository.get_articles_by_numbers(
                extracted_numbers, ley_o_codigo
            )
            sql_results = self._deduplicate_articles(
                sql_results, preferred_ley=ley_o_codigo
            )
            sql_results = self._apply_score_override(sql_results, extracted_numbers)

            def normalize_num(s: str) -> str:
                return re.sub(r"[^0-9]", "", s).lstrip("0")

            order_map = {normalize_num(n): i for i, n in enumerate(extracted_numbers)}
            sql_results.sort(
                key=lambda x: (
                    order_map.get(normalize_num(x.numero_articulo), 999),
                    -len(x.cuerpo_texto),
                )
            )

        query_enriquecida = f"""
Consulta legal: {consulta}
Materia jurídica: {materia_juridica or "No especificada"}
Contexto: Buscar artículos relevantes {"en " + ley_o_codigo if ley_o_codigo else "en toda la legislación"} con interpretación jurídica.
        """.strip()

        query_vector = await self.embedding_service.generate_embedding(
            query_enriquecida
        )

        top_k = (limite or 10) * 3
        semantic_results = await self.repository.search_similar_vectors(
            query_vector,
            top_k,
            materia_juridica=materia_juridica,
            ley_o_codigo=ley_o_codigo,
        )

        semantic_results = self._apply_score_override(
            semantic_results, extracted_numbers
        )

        all_results = sql_results + semantic_results
        all_results = self._deduplicate_articles(all_results)

        for entity in all_results:
            if entity.similitud != 0.99:
                content_lower = entity.cuerpo_texto.lower()
                query_terms = [t for t in consulta.lower().split() if len(t) > 3]
                score = entity.similitud or 0.0
                for term in query_terms:
                    if term in content_lower:
                        score += 0.04
                entity.similitud = round(min(score, 0.99), 4)

        all_results.sort(
            key=lambda x: (x.similitud or 0, -len(x.cuerpo_texto)), reverse=True
        )

        requested_count = len(extracted_numbers)
        if len(sql_results) >= requested_count:
            final_limit = limite or len(sql_results)
            return all_results[:final_limit]

        min_results = max(requested_count, 3)
        final_limit = limite or min(min_results, len(all_results))
        return all_results[:final_limit]

    async def _handle_semantic_intent(
        self,
        consulta: str,
        materia_juridica: Optional[str],
        ley_o_codigo: Optional[str],
        limite: Optional[int],
    ) -> List[ArticleEntity]:
        """Handle SEMANTIC intent: Vector search only."""
        query_vector = await self.embedding_service.generate_embedding(consulta)

        top_k = limite or 10
        semantic_results = await self.repository.search_similar_vectors(
            query_vector,
            top_k,
            materia_juridica=materia_juridica,
            ley_o_codigo=ley_o_codigo,
        )

        semantic_results.sort(key=lambda x: x.similitud or 0, reverse=True)

        return semantic_results
