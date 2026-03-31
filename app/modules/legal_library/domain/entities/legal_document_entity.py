import datetime
from dataclasses import dataclass
from typing import Optional


@dataclass
class LegalDocumentEntity:
    """
    Entidad representativa de un documento legal original (PDF, Boletín, Libro).
    """

    titulo: str
    nombre_archivo: str
    url_oficial: str
    url_interna: Optional[str] = None
    fecha_publicacion: Optional[str] = None
    fecha_ultima_reforma: Optional[str] = None
    fecha_carga: Optional[datetime.datetime] = None
    id: Optional[int] = None
