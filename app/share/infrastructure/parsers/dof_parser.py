import json
import logging
import os
import re
from typing import Dict, List, Optional

from bs4 import BeautifulSoup

from app.modules.legal_library.domain.services.document_parser import (
    DocumentParser,
    ParsedArticle,
)

logger = logging.getLogger("app.share.infrastructure.parsers.dof_parser")


def _load_materia_map() -> Dict[str, str]:
    """Carga el mapeo de nombre de ley a materia desde laws.json."""
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    laws_path = os.path.join(base_dir, "docs", "laws.json")

    materia_map = {}

    if os.path.exists(laws_path):
        try:
            with open(laws_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                urls = data.get("urls", {})

                for law_name in urls.keys():
                    law_lower = law_name.lower()
                    materias = _infer_materia_from_keywords(law_lower)
                    materia_map[law_name] = ", ".join(materias)

            logger.info(
                f"Cargados {len(materia_map)} mapeos de materias desde laws.json"
            )
        except Exception as e:
            logger.warning(f"Error cargando laws.json: {e}")
            materia_map = {}

    return materia_map


def _infer_materia_from_keywords(nombre_lower: str) -> List[str]:
    """Infiere la(s) materia(s) jurídica(s) basándose en keywords del nombre de la ley."""
    materias = set()

    if any(
        kw in nombre_lower
        for kw in [
            "penal",
            "delito",
            "cárcel",
            "prisión",
            "víctima",
            "imputado",
            "sentencia penal",
        ]
    ):
        materias.add("Penal")

    if any(
        kw in nombre_lower
        for kw in [
            "civil",
            "personas",
            "familia",
            "matrimonio",
            "divorcio",
            "tutela",
            "curatela",
            "patria potestad",
            "alimentos",
            "parentesco",
            "filiación",
            "adopción",
            "sucesiones",
            "herencia",
            "testamento",
            "legado",
            "obligaciones",
            "contratos",
            "bienes",
            "posesión",
            "usucapión",
            "hipoteca",
            "prenda",
            "servidumbre",
            "nuda propiedad",
            "usufructo",
        ]
    ):
        materias.add("Civil")

    if any(
        kw in nombre_lower
        for kw in [
            "trabajo",
            "laboral",
            "empleado",
            "patrón",
            "salario",
            "jornada",
            "vacaciones",
            "aguinaldo",
            "indemnización",
            "despido",
            "huelga",
            "sindicato",
            "contrato individual",
            "condiciones generales",
            "tiempoextra",
            "descanso",
            "maternal",
            "menor",
        ]
    ):
        materias.add("Laboral")

    if any(
        kw in nombre_lower
        for kw in [
            "seguridad social",
            "seguro social",
            "previsión social",
            "afiliación",
            "pensión",
            "jubilación",
            "vejez",
            "invalidez",
            "orfandad",
            "viudez",
            "issste",
            "imss",
            "sar",
            "infonavit",
            "cuenta individual",
            "servicio médico",
            "enfermedad",
            "ahorro para el retiro",
            "sistema de ahorro",
        ]
    ):
        materias.add("Seguridad Social")

    if any(
        kw in nombre_lower
        for kw in [
            "comercio",
            "mercantil",
            "comerciante",
            "acta constitutiva",
            "sociedad mercantil",
            "s.a.",
            "s.a.b.",
            "s. de r.l.",
            "s. en c.",
            "título de crédito",
            "letra de cambio",
            "pagaré",
            "cheque",
            " warrant",
            "corretaje",
            "comisión mercantil",
            "transporte",
            "depósito",
            "prenda civil",
        ]
    ):
        materias.add("Mercantil")

    if any(
        kw in nombre_lower
        for kw in [
            "fiscal",
            "tributari",
            "impuesto",
            "renta",
            "isr",
            "iva",
            "ieps",
            "ingresos",
            "aduana",
            "sat",
            "derechos",
            "contribuci",
            "fedatario",
            "generación de ingresos",
            "precio de transferencia",
            "consolidación fiscal",
        ]
    ):
        materias.add("Fiscal")

    if any(
        kw in nombre_lower
        for kw in [
            "amparo",
            "constitu",
            "derechos humanos",
            "garantías individuales",
            "principio constitucional",
            "reforma constitucional",
            "iniciativa",
            "poder legislativo",
            "poder ejecutivo",
            "poder judicial",
            "suprema corte",
            "tribunal electoral",
        ]
    ):
        materias.add("Constitucional")

    if any(
        kw in nombre_lower
        for kw in [
            "administrati",
            "función pública",
            "servidor público",
            "control administrativo",
            "responsabilidad administrativa",
            "bienes nacionales",
            "patrimonio federal",
            "adquisiciones",
            "obra pública",
            "recursos federales",
            "tribunal federal",
            "justicia administrativa",
        ]
    ):
        materias.add("Administrativo")

    if any(
        kw in nombre_lower
        for kw in [
            "bancario",
            "banco",
            "crédito",
            "inversión",
            "valores",
            "bolsa",
            "sistema financiero",
            "cnmv",
            "banco de méxico",
            "banxico",
            "intermediario",
            "aseguramiento",
            "fondos de inversión",
            "deuda",
        ]
    ):
        materias.add("Financiero")

    if any(
        kw in nombre_lower
        for kw in [
            "ambiental",
            "ecológico",
            "recursos naturales",
            "protección ambiental",
            "fauna",
            "flora",
            " áreas naturales",
            "manejo de residuos",
            "sustancias peligrosas",
            "emisiones",
            "cambio climático",
            "desarrollo sostenible",
        ]
    ):
        materias.add("Ambiental")

    if any(
        kw in nombre_lower
        for kw in [
            "energía",
            "petróleos",
            "petroleo",
            "gas natural",
            "electricidad",
            "hydrocarburo",
            "refinación",
            "pemex",
            "cenace",
            "cre",
            "hidroeléctrica",
            "eólica",
            "solar",
            "renovable",
        ]
    ):
        materias.add("Energético")

    if any(
        kw in nombre_lower
        for kw in [
            "comunicaciones",
            "telecomunicaciones",
            "telefonía",
            "radio",
            "televisión",
            "satélite",
            "internet",
            "correos",
            "ift",
            "telecom",
        ]
    ):
        materias.add("Telecomunicaciones")

    if any(
        kw in nombre_lower
        for kw in [
            "propiedad industrial",
            "propiedad intelectual",
            "patente",
            "marca",
            "derecho autor",
            "copyright",
            "modelo utilidad",
            "diseño industrial",
            "secreto industrial",
            "licencia",
        ]
    ):
        materias.add("Propiedad Intelectual")

    if any(
        kw in nombre_lower
        for kw in [
            "educativo",
            "educación",
            "educación pública",
            "institución educativa",
            "educación superior",
            "sep",
        ]
    ):
        materias.add("Educativo")

    if any(
        kw in nombre_lower
        for kw in [
            "salud",
            "médico",
            "sanitario",
            "epidemia",
            "epidemiológic",
            "hospital",
            "clínica",
            "medicamento",
            "dispositivo médico",
            "注册",
            "permiso sanitario",
            "comisión federal",
            "coepris",
        ]
    ):
        materias.add("Salud")

    if any(
        kw in nombre_lower
        for kw in [
            "agrario",
            "agrícola",
            "ejidal",
            "comunal",
            "tierra",
            "dotación",
            "restitución",
            "procede",
            "panel alfa",
        ]
    ):
        materias.add("Agrario")

    if any(
        kw in nombre_lower
        for kw in [
            "marítimo",
            "navegación",
            "puertos",
            "mar territorial",
            "aguas jurisdiccionales",
            "cabotaje",
            "admisión temporal",
            "arqueo",
        ]
    ):
        materias.add("Marítimo")

    if any(
        kw in nombre_lower
        for kw in [
            "aéreo",
            "aviación",
            "aeropuerto",
            "aeronave",
            "piloto",
            "navegación aérea",
            "sct",
            "dgac",
        ]
    ):
        materias.add("Aviación")

    if any(
        kw in nombre_lower
        for kw in [
            "ley orgánica",
            "reglamento interior",
            "municipio",
            "ayuntamiento",
            "seguridad pública",
            "protección civil",
            "adquisiciones públicas",
            "bienes muebles",
            "combate",
            "caminos",
            "puentes",
            "autotransporte",
            "transporte federal",
        ]
    ):
        materias.add("Administrativo")  # Gobierno cae en Administrativo

    if any(
        kw in nombre_lower
        for kw in [
            "patrimonio cultural",
            "patrimonio histórico",
            "patrimonio arqueológic",
        ]
    ):
        materias.add("Cultural")

    if not materias:
        materias.add("General")

    return sorted(list(materias))


class DOFHtmlParser(DocumentParser):
    """
    Parser robusto para HTMLs del DOF basado en texto (no DOM frágil).
    Optimizado para RAG (segmentación semántica + limpieza).
    """

    ARTICLE_PATTERN = re.compile(
        r"^\s*Art[ií]culo\s+([0-9]+(?:\s*(?:bis|ter|quater|quinquies))?[a-zºo]*)",
        re.IGNORECASE,
    )

    _materia_map: Dict[str, str] = {}

    def __init__(self):
        if not DOFHtmlParser._materia_map:
            DOFHtmlParser._materia_map = _load_materia_map()

    BOOK_PATTERN = re.compile(r"^LIBRO\s+(.+)$", re.IGNORECASE)
    TITLE_PATTERN = re.compile(r"^T[IÍ]TULO\s+(.+)$", re.IGNORECASE)
    CHAPTER_PATTERN = re.compile(r"^CAP[IÍ]TULO\s+(.+)$", re.IGNORECASE)
    TRANSITORY_PATTERN = re.compile(r"^TRANSITORIOS?$", re.IGNORECASE)

    NOISE_PATTERNS = [
        re.compile(r"^al\s+margen\s+un\s+sello", re.IGNORECASE),
        re.compile(r"^diario\s+oficial\s+de\s+la\s+federaci[oó]n", re.IGNORECASE),
        re.compile(r"^p[aá]gina\s+\d+", re.IGNORECASE),
    ]

    # 🔥 FIX: romanos ilimitados
    FRACTION_PATTERN = re.compile(r"\b([IVXLCDM]+)\.\s")

    def parse(self, content: str) -> List[ParsedArticle]:
        soup = BeautifulSoup(content, "html.parser")

        ley_nombre = self._extract_law_name(soup)
        paragraphs = self._normalize_html(soup)

        articles = self._extract_articles(paragraphs, ley_nombre)

        logger.info(f"Parser DOF extrajo {len(articles)} artículos de '{ley_nombre}'")
        return articles

    # =========================
    # NORMALIZACIÓN
    # =========================
    def _normalize_html(self, soup: BeautifulSoup) -> list[str]:
        paragraphs = []

        for element in soup.find_all(["p", "li"]):
            text = element.get_text(" ", strip=True)

            if not text:
                continue

            text = text.replace("\xa0", " ")
            text = re.sub(r"\s+", " ", text)

            if self._is_noise_paragraph(text):
                continue

            paragraphs.append(text)

        return paragraphs

    def _is_noise_paragraph(self, text: str) -> bool:
        text_lower = text.lower().strip()
        if not text_lower:
            return True

        for pattern in self.NOISE_PATTERNS:
            if pattern.search(text_lower):
                return True

        return False

    # =========================
    # LEY
    # =========================
    def _extract_law_name(self, soup: BeautifulSoup) -> str:
        golden = soup.find("span", style=re.compile(r"color:\s*#A6802D", re.IGNORECASE))
        if golden:
            return golden.get_text(strip=True)

        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)

        if soup.title and soup.title.get_text(strip=True):
            title_text = soup.title.get_text(strip=True)
            if len(title_text) > 12:
                return title_text

        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if self.BOOK_PATTERN.match(text):
                continue
            if self.TITLE_PATTERN.match(text):
                continue
            if self.CHAPTER_PATTERN.match(text):
                continue
            if text.upper().startswith("ART"):
                continue
            if len(text) > 10 and text.isupper():
                return text

        return "Ley Desconocida"

    # =========================
    # ARTÍCULOS
    # =========================
    def _extract_articles(
        self, paragraphs: list[str], ley_nombre: str
    ) -> list[ParsedArticle]:

        articles = []
        current_book = None
        current_title = None

        current_article = None
        buffer = []
        in_transitory_section = False

        for text in paragraphs:
            if self.TRANSITORY_PATTERN.match(text):
                in_transitory_section = True
                continue

            if in_transitory_section:
                continue

            if self.BOOK_PATTERN.match(text):
                current_book = text
                continue

            if self.TITLE_PATTERN.match(text):
                current_title = text
                continue

            if self.CHAPTER_PATTERN.match(text):
                continue

            art_match = self.ARTICLE_PATTERN.match(text)

            if art_match:
                if current_article and buffer:
                    built_article = self._build_article(
                        current_article,
                        buffer,
                        ley_nombre,
                        current_book,
                        current_title,
                    )
                    if built_article.cuerpo_texto:
                        articles.append(built_article)

                numero_raw = art_match.group(1)

                numero_clean = self._normalize_article_number(numero_raw)

                current_article = numero_clean
                buffer = []

                clean_text = re.sub(
                    r"^\s*Art[ií]culo\s+[0-9]+(?:\s*(?:bis|ter|quater|quinquies))?[a-zºo]*[\.\-–—:\s]*",
                    "",
                    text,
                    flags=re.IGNORECASE,
                ).strip()

                if clean_text:
                    buffer.append(clean_text)

                continue

            if "reformado" in text.lower() or "adicionado" in text.lower():
                continue

            if current_article:
                buffer.append(text)

        if current_article and buffer:
            built_article = self._build_article(
                current_article,
                buffer,
                ley_nombre,
                current_book,
                current_title,
            )
            if built_article.cuerpo_texto:
                articles.append(built_article)

        return articles

    def _normalize_article_number(self, raw_number: str) -> str:
        normalized = re.sub(r"\s+", " ", raw_number).strip().upper()
        normalized = normalized.replace("º", "")
        normalized = re.sub(r"(?<=\d)O$", "", normalized)
        return normalized

    # =========================
    # BUILDER
    # =========================
    def _build_article(
        self,
        numero: str,
        buffer: List[str],
        ley_nombre: str,
        current_book: Optional[str],
        current_title: Optional[str],
    ) -> ParsedArticle:

        body = " ".join(buffer)
        body = re.sub(r"\s+", " ", body).strip()

        # limpieza final
        body = re.sub(r"^\.\-\s*", "", body)
        body = re.sub(r"\s+;", ";", body)
        body = re.sub(r"\s+,", ",", body)

        if len(body) < 20:
            body = ""

        return ParsedArticle(
            materia_juridica=self._infer_materia(ley_nombre),
            ley_o_codigo=ley_nombre,
            libro_o_titulo=current_title or current_book,
            numero_articulo=f"Art. {numero}",
            cuerpo_texto=body,
        )

    # =========================
    # 🔥 RAG CHUNKING PRO
    # =========================
    def split_for_rag(self, article: ParsedArticle):
        """
        Divide artículos en chunks semánticos:
        - Proemio (contexto general)
        - Fracciones (unidad legal real)
        """

        text = article.cuerpo_texto.strip()

        parts = self.FRACTION_PATTERN.split(text)

        chunks = []

        # =========================
        # 🔥 FIX: PROEMIO
        # =========================
        proemio = parts[0].strip()

        if proemio:
            chunks.append(
                {
                    "articulo": article.numero_articulo,
                    "fraccion": None,
                    "tipo": "proemio",
                    "texto": proemio,
                }
            )

        # =========================
        # FRACCIONES
        # =========================
        for i in range(1, len(parts), 2):
            numeral = parts[i]
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""

            if not content:
                continue

            chunks.append(
                {
                    "articulo": article.numero_articulo,
                    "fraccion": numeral,
                    "tipo": "fraccion",
                    "texto": content,
                }
            )

        return chunks

    # =========================
    # MATERIA
    # =========================
    def _infer_materia(self, ley_nombre: str) -> List[str]:
        if ley_nombre in self._materia_map:
            # The cached value is comma-separated string, convert back to list
            return [m.strip() for m in self._materia_map[ley_nombre].split(",")]

        nombre_lower = ley_nombre.lower()
        return _infer_materia_from_keywords(nombre_lower)


# instancia global
dof_parser = DOFHtmlParser()
