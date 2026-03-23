import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger("app.core.dof_parser")

class DOFParser:
    """
    Parser determinístico para HTMLs exportados del DOF (Diario Oficial de la Federación).
    Extrae artículos, libros, títulos y el nombre de la ley sin usar IA.
    """

    ARTICLE_PATTERN = re.compile(r"Art[ií]culo\s+(\d+[a-z]?)[\.\s]*-?\s*", re.IGNORECASE)
    BOOK_PATTERN = re.compile(r"^LIBRO\s+(.+)$", re.IGNORECASE)
    TITLE_PATTERN = re.compile(r"^T[IÍ]TULO\s+(.+)$", re.IGNORECASE)
    CHAPTER_PATTERN = re.compile(r"^CAP[IÍ]TULO\s+(.+)$", re.IGNORECASE)

    def parse(self, html_content: str) -> list[dict]:
        soup = BeautifulSoup(html_content, "html.parser")

        ley_nombre = self._extract_law_name(soup)
        articles = self._extract_articles(soup, ley_nombre)

        logger.info(f"Parser DOF extrajo {len(articles)} artículos de '{ley_nombre}'")
        return articles

    def _extract_law_name(self, soup: BeautifulSoup) -> str:
        """Busca el nombre de la ley por su color dorado característico del DOF (#A6802D)."""
        golden = soup.find("span", style=re.compile(r"color:\s*#A6802D", re.IGNORECASE))
        if golden:
            return golden.get_text(strip=True)

        # Fallback: buscar el primer <b> centrado que no sea vacío
        for p in soup.find_all("p", style=re.compile(r"text-align:\s*center")):
            bold = p.find("b")
            if bold:
                text = bold.get_text(strip=True)
                if len(text) > 5:
                    return text

        return "Ley Desconocida"

    def _extract_articles(self, soup: BeautifulSoup, ley_nombre: str) -> list[dict]:
        articles = []
        current_book = None
        current_title = None

        paragraphs = soup.find_all("p")

        i = 0
        while i < len(paragraphs):
            p = paragraphs[i]
            text = p.get_text(strip=True)

            if not text or text == "\xa0":
                i += 1
                continue

            # Detectar Libro
            book_match = self.BOOK_PATTERN.match(text)
            if book_match:
                current_book = text
                i += 1
                continue

            # Detectar Título
            title_match = self.TITLE_PATTERN.match(text)
            if title_match:
                current_title = text
                i += 1
                continue

            # Detectar Capítulo (lo guardamos como parte del título)
            chapter_match = self.CHAPTER_PATTERN.match(text)
            if chapter_match:
                i += 1
                continue

            # Detectar Artículo
            bold = p.find("b")
            if bold:
                bold_text = bold.get_text(strip=True)
                art_match = self.ARTICLE_PATTERN.match(bold_text)
                if art_match:
                    numero = f"Art. {art_match.group(1)}"

                    # El cuerpo es todo el texto del párrafo menos el encabezado del artículo
                    full_text = p.get_text(strip=True)
                    body = self.ARTICLE_PATTERN.sub("", full_text, count=1).strip()

                    # Recolectar párrafos subsiguientes hasta el siguiente artículo/título/libro
                    i += 1
                    while i < len(paragraphs):
                        next_p = paragraphs[i]
                        next_text = next_p.get_text(strip=True)

                        if not next_text or next_text == "\xa0":
                            i += 1
                            continue

                        # Si es nota de reforma (color guinda), la ignoramos
                        reform_span = next_p.find("span", style=re.compile(r"color:\s*#740033", re.IGNORECASE))
                        if reform_span and reform_span.get_text(strip=True) == next_text:
                            i += 1
                            continue

                        # Si es un nuevo artículo, libro o título, paramos
                        next_bold = next_p.find("b")
                        if next_bold:
                            nb_text = next_bold.get_text(strip=True)
                            if (self.ARTICLE_PATTERN.match(nb_text) or
                                self.BOOK_PATTERN.match(nb_text) or
                                self.TITLE_PATTERN.match(nb_text) or
                                self.CHAPTER_PATTERN.match(nb_text)):
                                break

                        body += " " + next_text
                        i += 1

                    if body:
                        articles.append({
                            "materia_juridica": self._infer_materia(ley_nombre),
                            "ley_o_codigo": ley_nombre,
                            "libro_o_titulo": current_book or current_title,
                            "numero_articulo": numero,
                            "cuerpo_texto": body.strip(),
                        })
                    continue

            i += 1

        return articles

    def _infer_materia(self, ley_nombre: str) -> str:
        """Infiere la materia jurídica a partir del nombre de la ley."""
        nombre_lower = ley_nombre.lower()
        if "penal" in nombre_lower:
            return "Penal"
        elif "civil" in nombre_lower:
            return "Civil"
        elif "trabajo" in nombre_lower or "laboral" in nombre_lower:
            return "Laboral"
        elif "comercio" in nombre_lower or "mercantil" in nombre_lower:
            return "Mercantil"
        elif "fiscal" in nombre_lower or "tributari" in nombre_lower:
            return "Fiscal"
        elif "amparo" in nombre_lower:
            return "Constitucional"
        elif "constituc" in nombre_lower:
            return "Constitucional"
        elif "administrat" in nombre_lower:
            return "Administrativo"
        return "General"


# Instancia global reutilizable
dof_parser = DOFParser()
