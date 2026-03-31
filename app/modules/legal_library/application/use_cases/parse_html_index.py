import logging
import re
from typing import Dict

from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger("app.legal_library.use_cases.parse_html_index")


class ParseHtmlIndexUseCase:
    """
    Caso de uso para parsear la tabla HTML de ordenjuridico.gob.mx
    y retornar un diccionario con el formato solicitado:
    nombre: { id: "url", fecha_de_publicacion: "str", fecha_de_ultima_reforma: "str" }
    """

    def execute(
        self, html_content: str, base_url: str = settings.ORDEN_JURIDICO_URL
    ) -> Dict[str, Dict]:
        soup = BeautifulSoup(html_content, "html.parser")
        results = {}

        # Buscar todos los tr (table rows)
        for tr in soup.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) >= 4:
                # El segundo td tiene el <a> con el nombre y el id (href)
                a_tag = tds[1].find("a")
                if a_tag:
                    nombre = a_tag.get_text(strip=True)
                    # Limpiamos el nombre
                    nombre = re.sub(r"\s+", " ", nombre).strip()

                    # El ID o HRF está en el atributo 'id' (".././Documentos/Federal/wo17186.doc") o 'href'
                    raw_path = a_tag.get("id") or a_tag.get("href", "")

                    # Limpiar el path: quitar '.././' y reemplazar '.doc' con '.html'
                    clean_path = (
                        raw_path.replace(".././", "")
                        .replace("../", "")
                        .replace("./", "")
                    )
                    if clean_path.endswith(".doc"):
                        clean_path = clean_path[:-4] + ".html"

                    clean_path = clean_path.replace(
                        "Documentos/Federal/", "Documentos/Federal/html/"
                    )

                    full_url = f"{base_url.rstrip('/')}/{clean_path.lstrip('/')}"

                    # Tercer td: fecha de publicacion
                    fecha_pub = tds[2].get_text(strip=True)

                    # Cuarto td: fecha de ultima reforma
                    fecha_ref = tds[3].get_text(strip=True)

                    if nombre:
                        results[nombre] = {
                            "id": full_url,
                            "fecha_de_publicacion": fecha_pub,
                            "fecha_de_ultima_reforma": fecha_ref,
                        }

        logger.info(f"Se parsearon {len(results)} documentos de la tabla HTML.")
        results = {"urls": results}
        return results
