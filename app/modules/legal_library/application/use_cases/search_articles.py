import logging
import re
from typing import List, Optional

from app.modules.legal_library.adapters.app_domain_mapper import \
    AppDomainMapper
from app.modules.legal_library.application.schemas.article_app_schemas import \
    ArticleAppOutputDTO
from app.modules.legal_library.domain.repositories.legal_repository import \
    LegalRepository
from app.modules.legal_library.domain.services.embedding_service import \
    EmbeddingService
from app.modules.legal_library.domain.services.legal_router_service import \
    LegalRouterService
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
        """Extrae números de artículos (Dígitos y Palabras) para máxima robustez."""
        # Normalizamos acentos y pasamos a lower
        q_norm = query.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        # Mapeo de palabras a números (Caso 9 Error Humano)
        word_to_num = {
            "uno": "1", "dos": "2", "tres": "3", "cuatro": "4", "cinco": "5",
            "seis": "6", "siete": "7", "ocho": "8", "nueve": "9", "diez": "10",
        }
        
        # Primero reemplazamos palabras por dígitos solo si vienen después de "artículo"
        for word, num in word_to_num.items():
            q_norm = re.sub(rf"(articulo\s+){word}\b", rf"\g<1>{num}", q_norm)

        # Pattern que busca "art", "articulo", "articulos" seguido de secuencias numéricas
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
        return [x for x in numbers if not (x in seen or seen.add(x))]

    def _extract_law_name(self, query: str) -> Optional[str]:
        """Infiere el nombre de la ley/código mencionado en la consulta (RAG Intelligence)."""
        # Normalizamos para búsqueda de ley (sin acentos en los alias para mayor recall)
        q_norm = query.upper().replace("Á", "A").replace("É", "E").replace("Í", "I").replace("Ó", "O").replace("Ú", "U")

        laws_map = {
            "CODIGO CIVIL FEDERAL": "CÓDIGO CIVIL FEDERAL",
            "CIVIL FEDERAL": "CÓDIGO CIVIL FEDERAL",
            "CCF": "CÓDIGO CIVIL FEDERAL",
            "CODIGO DE COMERCIO": "CÓDIGO DE COMERCIO",
            "COMERCIO": "CÓDIGO DE COMERCIO",
            "CODIGO PENAL": "CÓDIGO PENAL FEDERAL",
            "LEY DE AMPARO": "Ley de Amparo, Reglamentaria de los Artículos 103 y 107 de la Constitución Política de los Estados Unidos Mexicanos",
            "AMPARO": "Ley de Amparo, Reglamentaria de los Artículos 103 y 107 de la Constitución Política de los Estados Unidos Mexicanos",
            "LEY FEDERAL DEL TRABAJO": "Ley Federal del Trabajo",
            "TRABAJO": "Ley Federal del Trabajo",
            "TRABAJADOR": "Ley Federal del Trabajo",
            "LEY GENERAL DE EDUCACION": "Ley General de Educación",
            "EDUCACION": "Ley General de Educación",
            "LEY GENERAL DE SALUD": "Ley General de Salud",
            "SALUD": "Ley General de Salud",
            "LEY AGRARIA": "Ley Agraria",
            "AGRARIA": "Ley Agraria",
            "LEY DE INSTITUCIONES DE CREDITO": "Ley de Instituciones de Crédito",
            "CREDITO": "Ley de Instituciones de Crédito",
            "NACIONAL DE EXTINCION DE DOMINIO": "Ley Nacional de Extinción de Dominio",
            "EXTINCION DE DOMINIO": "Ley Nacional de Extinción de Dominio",
            "PROTECCION DE DATOS": "Ley Federal de Protección de Datos Personales en Posesión de los Particulares",
            "ORGANICA DEL PODER JUDICIAL": "Ley Orgánica del Poder Judicial de la Federación",
            "MERCADO DE VALORES": "Ley del Mercado de Valores",
            "CONTRATO DE SEGURO": "Ley sobre el Contrato de Seguro",
            "DERECHO DE AUTOR": "Ley Federal del Derecho de Autor",
            "AGUAS NACIONALES": "Ley de Aguas Nacionales",
            "INGRESOS SOBRE HIDROCARBUROS": "Ley de Ingresos sobre Hidrocarburos",
            "JUSTICIA MILITAR": "Código de Justicia Militar",
        }

        # Match de alias orientado a precisión (más largo primero)
        sorted_keys = sorted(laws_map.keys(), key=len, reverse=True)
        for term in sorted_keys:
            # Buscamos el término como palabra delimitada para evitar falsos positivos (Grave #4)
            if re.search(rf"\b{term}\b", q_norm):
                official = laws_map[term]
                logger.info(f"Detección de Ley (Senior): '{term}' -> '{official}'")
                return official

        return None

    def _determine_intent(self, query: str, numbers: List[str], law_detected: Optional[str] = None) -> str:
        """Determina la intención con precisión legal (Senior UX)."""
        if not numbers:
            return "semantic"

        q_lower = query.lower()

        # Palabras clave semánticas
        semantic_keywords = [
            "explica", "relacion", "diferencia", "comparar", "ejemplo",
            "interpretación", "caso", "aplica", "porque", "por que",
            "cómo", "como", "cuándo", "cuando", "qué establece", 
            "que establece", "qué dice", "que dice",
        ]

        # Si hay números Y ley explícita, es DIRECTA a menos que haya carga semántica pesada
        has_semantic_intent = any(k in q_lower for k in semantic_keywords)
        
        if has_semantic_intent:
            return "hybrid"

        # Si hay ley y artículos -> 100% Directo (Senior Fix #2)
        if law_detected:
            return "direct"

        return "hybrid" if len(numbers) > 0 else "semantic"

    async def execute(
        self,
        consulta: str,
        limite: Optional[int] = None,
        materia_juridica: str | None = None,
        ley_o_codigo: str | None = None,
    ) -> list[ArticleAppOutputDTO]:
        try:
            # 1. Parámetros dinámicos (Senior Fix #3)
            # Si el usuario no pide un límite específico, buscamos 15 pero filtraremos dinámicamente.
            search_limit = limite or 15
            
            # --- Inferencia de Ley (RAG Intelligence) ---
            inferred_law = self._extract_law_name(consulta)
            if not ley_o_codigo and inferred_law:
                ley_o_codigo = inferred_law

            extracted_numbers = self._extract_article_numbers(consulta)
            intent = self._determine_intent(consulta, extracted_numbers, inferred_law)
            
            if not ley_o_codigo and intent != "semantic":
                ley_o_codigo = "CÓDIGO CIVIL FEDERAL"

            # 2. Router: Detección de materia
            if not materia_juridica:
                materia_juridica = await self.router_service.detect_materia(consulta)
            
            if inferred_law:
                logger.info(f"Omitiendo filtro de materia por detección de ley: {inferred_law}")
                materia_juridica = None

            # Debug logs para validación de suite
            logger.info(
                f"Búsqueda | Intent: {intent} | Context: {ley_o_codigo or 'Global'} | Query: {consulta}"
            )

            entities = []

            # --- RUTA ESTRUCTURADA (SQL Bypass) ---
            sql_results = []
            if extracted_numbers and ley_o_codigo:
                sql_results = await self.repository.get_articles_by_numbers(
                    extracted_numbers, ley_o_codigo
                )

                # Preservar el orden solicitado y deduplicar shards (Senior Fix #3)
                def normalize_num(s: str) -> str:
                    return re.sub(r"[^0-9]", "", s).lstrip("0")

                order_map = {normalize_num(n): i for i, n in enumerate(extracted_numbers)}
                sql_results.sort(key=lambda x: order_map.get(normalize_num(x.numero_articulo), 999))
                
                seen_articles = set()
                deduplicated_sql = []
                for res in sql_results:
                    key = (res.ley_o_codigo.lower(), res.numero_articulo.lower())
                    if key not in seen_articles:
                        seen_articles.add(key)
                        res.similitud = 0.99
                        deduplicated_sql.append(res)
                
                sql_results = deduplicated_sql

            # --- DECISIÓN DE FLUJO ---
            if intent == "direct" and sql_results:
                entities = sql_results
            else:
                # --- RUTA SEMÁNTICA (Vector Search) ---
                query_enriquecida = f"""
Consulta legal: {consulta}
Materia jurídica: {materia_juridica or "No especificada"}
Contexto: Buscar artículos relevantes {'en ' + ley_o_codigo if ley_o_codigo else 'en toda la legislación'} con interpretación jurídica.
""".strip()

                query_vector = await self.embedding_service.generate_embedding(
                    query_enriquecida
                )

                # Usamos search_limit ampliado para el re-ranking
                top_k_vector = search_limit * 3
                semantic_results = await self.repository.search_similar_vectors(
                    query_vector,
                    top_k_vector,
                    materia_juridica=materia_juridica,
                    ley_o_codigo=ley_o_codigo,
                )

                # --- MERGE INTELIGENTE ---
                seen_keys = set()
                merged_list = []
                for e in sql_results + semantic_results:
                    key = (e.ley_o_codigo.lower(), e.numero_articulo.lower())
                    if key not in seen_keys:
                        seen_keys.add(key)
                        merged_list.append(e)

                entities = merged_list

                # --- RE-RANKING HÍBRIDO ---
                def calculate_boosted_score(entity) -> float:
                    if entity.similitud == 0.99:
                        return 0.99

                    score = entity.similitud or 0.0
                    content_lower = entity.cuerpo_texto.lower()
                    query_terms = [t for t in consulta.lower().split() if len(t) > 3]

                    for term in query_terms:
                        if term in content_lower:
                            score += 0.04

                    for n_str in extracted_numbers:
                        if n_str.lower() in entity.numero_articulo.lower():
                            score = max(score, 0.92)

                    entity.similitud = round(score, 4)
                    return score

                entities.sort(key=calculate_boosted_score, reverse=True)

            # --- CORTE INTELIGENTE (Opción 3: Dynamic Top-K) ---
            # 1. Resultados de Alta Confianza (Estructural o > 0.82)
            high_quality = [e for e in entities if e.similitud >= 0.82]
            
            # 2. Resultados de Relevancia Media (Base semántica decente)
            mid_quality = [e for e in entities if 0.70 <= e.similitud < 0.82]
            
            # Decidimos qué tan "honesto" ser basado en la densidad de resultados
            if high_quality:
                # Si hay calidad alta, mostramos todo lo bueno + opcionalmente un poco de ruido si se pidió explícitamente limit
                filtered_entities = high_quality
                if len(filtered_entities) < 3:
                     # Completamos con los siguientes mejores hasta 3 si superan el suelo de ruido.
                     filtered_entities += mid_quality[:3 - len(filtered_entities)]
            else:
                # Si no hay nada "excelente", mostramos los top 3 que superen el suelo 0.70
                filtered_entities = mid_quality[:3]

            # Si el usuario pidió un límite específico, forzamos el recorte superior.
            final_limit = limite or len(filtered_entities)
            final_entities = filtered_entities[:final_limit]

            return [AppDomainMapper.domain_to_app_output(e) for e in final_entities]

        except Exception as e:
            # Registro detallado del error para depuración en producción
            logger.error(
                f"Error crítico en HybridSearch | Query: '{consulta}' | Error: {str(e)}",
                exc_info=True,
            )
            if "openai" in str(e).lower() or "asyncpg" in str(e).lower():
                # Propagamos excepciones conocidas para que el handler global las gestione
                raise
            raise InfrastructureException(
                message=f"Error durante el procesamiento de la búsqueda legal: {str(e)}",
                code="HYBRID_SEARCH_FAILURE",
            )
