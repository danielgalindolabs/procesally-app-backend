from abc import ABC, abstractmethod
from typing import Optional


class LegalRouterService(ABC):
    """
    Servicio de Dominio encargado de decidir qué filtros aplicar a una consulta
    en base a su contenido semántico o heurístico.
    """

    @abstractmethod
    async def detect_materia(self, query: str) -> Optional[str]:
        """
        Analiza la consulta y devuelve la materia jurídica detectada (ej. 'Civil', 'Laboral').
        Retorna None si no se puede determinar con confianza.
        """
        pass
