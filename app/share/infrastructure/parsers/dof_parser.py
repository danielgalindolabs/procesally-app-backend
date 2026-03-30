import logging
import re

from bs4 import BeautifulSoup

from app.modules.legal_library.domain.services.document_parser import (
    DocumentParser,
    ParsedArticle,
)

logger = logging.getLogger("app.share.infrastructure.parsers.dof_parser")


class DOFHtmlParser(DocumentParser):
    """
    Parser robusto para HTMLs del DOF basado en texto (no DOM frágil).
    Optimizado para RAG (segmentación semántica + limpieza).
    """

    ARTICLE_PATTERN = re.compile(r"Art[ií]culo\s+(\d+[a-zºo]*)", re.IGNORECASE)

    BOOK_PATTERN = re.compile(r"^LIBRO\s+(.+)$", re.IGNORECASE)
    TITLE_PATTERN = re.compile(r"^T[IÍ]TULO\s+(.+)$", re.IGNORECASE)
    CHAPTER_PATTERN = re.compile(r"^CAP[IÍ]TULO\s+(.+)$", re.IGNORECASE)

    # 🔥 FIX: romanos ilimitados
    FRACTION_PATTERN = re.compile(r"\b([IVXLCDM]+)\.\s")

    def parse(self, content: str) -> list[ParsedArticle]:
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

        for p in soup.find_all("p"):
            text = p.get_text(" ", strip=True)

            if not text:
                continue

            text = text.replace("\xa0", " ")
            text = re.sub(r"\s+", " ", text)

            paragraphs.append(text)

        return paragraphs

    # =========================
    # LEY
    # =========================
    def _extract_law_name(self, soup: BeautifulSoup) -> str:
        golden = soup.find("span", style=re.compile(r"color:\s*#A6802D", re.IGNORECASE))
        if golden:
            return golden.get_text(strip=True)

        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
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

        for text in paragraphs:

            if self.BOOK_PATTERN.match(text):
                current_book = text
                continue

            if self.TITLE_PATTERN.match(text):
                current_title = text
                continue

            if self.CHAPTER_PATTERN.match(text):
                continue

            # 🔥 FIX: search
            art_match = self.ARTICLE_PATTERN.search(text)

            if art_match:
                if current_article and buffer:
                    articles.append(
                        self._build_article(
                            current_article,
                            buffer,
                            ley_nombre,
                            current_book,
                            current_title,
                        )
                    )

                numero_raw = art_match.group(1)

                # 🔥 normalización robusta
                numero_clean = numero_raw.replace("º", "").replace("o", "")

                current_article = numero_clean
                buffer = []

                clean_text = re.sub(
                    r"^Art[ií]culo\s+\d+[a-zºo]*[\.\-\s]*",
                    "",
                    text,
                    flags=re.IGNORECASE,
                ).strip()

                if clean_text:
                    buffer.append(clean_text)

                continue

            # ruido DOF
            if "reformado" in text.lower() or "adicionado" in text.lower():
                continue

            if current_article:
                buffer.append(text)

        if current_article and buffer:
            articles.append(
                self._build_article(
                    current_article,
                    buffer,
                    ley_nombre,
                    current_book,
                    current_title,
                )
            )

        return articles

    # =========================
    # BUILDER
    # =========================
    def _build_article(
        self,
        numero: str,
        buffer: list[str],
        ley_nombre: str,
        current_book: str | None,
        current_title: str | None,
    ) -> ParsedArticle:

        body = " ".join(buffer)
        body = re.sub(r"\s+", " ", body).strip()

        # limpieza final
        body = re.sub(r"^\.\-\s*", "", body)

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
    def _infer_materia(self, ley_nombre: str) -> str:
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
        elif "amparo" in nombre_lower or "constituc" in nombre_lower:
            return "Constitucional"
        elif "administrat" in nombre_lower:
            return "Administrativo"

        return "General"


# instancia global
dof_parser = DOFHtmlParser()
