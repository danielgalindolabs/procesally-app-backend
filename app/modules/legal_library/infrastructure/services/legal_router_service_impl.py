import re
from typing import Optional

from app.modules.legal_library.domain.services.legal_router_service import (
    LegalRouterService,
)
from app.modules.share.infrastructure.services.embedding_service import engine


class LegalRouterServiceImpl(LegalRouterService):
    """
    Motor híbrido de decisión de materia jurídica:
    1. Heurísticas (Regex/Palabras clave)
    2. LLM (GPT via OpenAI) - Opcional / Futuro
    """

    CATEGORIES = ["Civil", "Laboral", "Penal", "Fiscal"]

    # Mapeo de palabras clave para Heurísticas rápidas
    HEURISTICS = {
        "Laboral": [
            "patrón",
            "trabajador",
            "despido",
            "salario",
            "sindicato",
            "huelga",
            "finiquito",
            "vacaciones",
        ],
        "Fiscal": [
            "impuesto",
            "SAT",
            "hacienda",
            "ISR",
            "IVA",
            "contributivo",
            "multa",
        ],
        "Penal": ["delito", "prisión", "cárcel", "homicidio", "robo", "fiscalía", "MP"],
        "Civil": [
            "matrimonio",
            "divorcio",
            "contrato",
            "herencia",
            "testamento",
            "daño",
        ],
    }

    async def detect_materia(self, query: str) -> Optional[str]:
        # 1. Intento por Heurísticas (Rápido y barato)
        lower_query = query.lower()
        for materia, keywords in self.HEURISTICS.items():
            if any(re.search(rf"\b{kw}\b", lower_query) for kw in keywords):
                return materia

        # 2. Intento por LLM (Más preciso pero requiere llamada API)
        # Por ahora usamos una lógica simplificada o podemos llamar a ChatGPT
        # para que nos de la categoría basado en el contexto.
        try:
            # Reutilizamos el cliente de OpenAI del motor de embeddings
            client = engine.client
            prompt = f"""
            Clasifica la siguiente consulta legal en una de estas categorías: {", ".join(self.CATEGORIES)}.
            Si no estás seguro, responde 'None'.
            Consulta: "{query}"
            Respuesta (solo la palabra de la categoría o 'None'):
            """

            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0,
            )

            detected = response.choices[0].message.content.strip()
            if detected in self.CATEGORIES:
                return detected
        except Exception:
            pass

        return None
