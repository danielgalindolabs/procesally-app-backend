import logging
import random
from collections import defaultdict

from app.modules.legal_library.application.schemas.article_app_schemas import (
    BulkUrlIngestAppInputDTO,
    BulkUrlSampleOptionsAppInputDTO,
    DocumentAppInputDTO,
)
from app.modules.legal_library.application.use_cases.bulk_ingest import (
    BulkIngestUseCase,
)
from app.modules.legal_library.domain.services.document_downloader import (
    DocumentDownloader,
)
from app.modules.share.infrastructure.parsers.dof_parser import (
    _infer_materia_from_keywords,
)

logger = logging.getLogger("app.legal_library.use_cases.bulk_url_ingest_dev_sample")


class BulkUrlIngestDevSampleUseCase:
    """Ingesta de muestra para desarrollo, orientada a diversidad y ligereza."""

    def __init__(
        self,
        bulk_ingest_uc: BulkIngestUseCase,
        document_downloader: DocumentDownloader,
    ):
        self.bulk_ingest_uc = bulk_ingest_uc
        self.document_downloader = document_downloader

    async def execute(
        self,
        input_dto: BulkUrlIngestAppInputDTO,
        options: BulkUrlSampleOptionsAppInputDTO,
    ) -> dict:
        candidates = self._build_candidates(input_dto)
        candidates = await self._attach_content_lengths(candidates)
        selected_candidates = self._select_candidates(candidates, options)

        if options.dry_run:
            return {
                "modo": options.modo,
                "target_articulos": options.target_articulos,
                "max_articulos_por_ley": options.max_articulos_por_ley,
                "max_leyes": options.max_leyes,
                "dry_run": True,
                "leyes_seleccionadas": len(selected_candidates),
                "distribucion_materias": self._materia_distribution(
                    selected_candidates
                ),
                "detalles_leyes": [
                    {
                        "titulo": c["titulo"],
                        "url": c["url"],
                        "materia_principal": c["materia_principal"],
                        "content_length": c["content_length"],
                    }
                    for c in selected_candidates
                ],
            }

        processed_laws = 0
        inserted_articles = 0
        success_count = 0
        failure_count = 0
        details = {}

        for candidate in selected_candidates:
            if inserted_articles >= options.target_articulos:
                break

            remaining = options.target_articulos - inserted_articles
            per_law_limit = min(options.max_articulos_por_ley, remaining)

            try:
                content = await self.document_downloader.fetch_content(candidate["url"])

                metadata = DocumentAppInputDTO(
                    titulo=candidate["titulo"],
                    nombre_archivo=(
                        candidate["url"].split("/")[-1] or f"{candidate['titulo']}.html"
                    ),
                    url_oficial=candidate["url"],
                    url_interna=None,
                    fecha_publicacion=candidate["fecha_pub"],
                    fecha_ultima_reforma=candidate["fecha_ref"],
                )

                result = await self.bulk_ingest_uc.execute(
                    content=content,
                    archivo_url=candidate["url"],
                    document_metadata=metadata,
                    max_articles=per_law_limit,
                )

                inserted = int(result.get("insertados", 0))
                inserted_articles += inserted
                processed_laws += 1
                success_count += 1
                details[candidate["titulo"]] = result
            except Exception as e:
                failure_count += 1
                processed_laws += 1
                details[candidate["titulo"]] = {"error": str(e)}
                logger.error(
                    "Error en muestra dev para %s: %s",
                    candidate["titulo"],
                    e,
                )

        return {
            "resumen_general": {
                "modo": options.modo,
                "target_articulos": options.target_articulos,
                "insertados": inserted_articles,
                "leyes_seleccionadas": len(selected_candidates),
                "leyes_procesadas": processed_laws,
                "exitosos": success_count,
                "fallidos": failure_count,
                "distribucion_materias": self._materia_distribution(
                    selected_candidates
                ),
            },
            "detalles": details,
        }

    def _build_candidates(self, input_dto: BulkUrlIngestAppInputDTO) -> list[dict]:
        candidates = []

        for titulo, info in input_dto.urls.items():
            materias = _infer_materia_from_keywords(titulo.lower())
            materia_principal = materias[0] if materias else "General"
            candidates.append(
                {
                    "titulo": titulo,
                    "url": info["url"],
                    "fecha_pub": info.get("fecha_pub"),
                    "fecha_ref": info.get("fecha_ref"),
                    "materias": materias,
                    "materia_principal": materia_principal,
                    "content_length": None,
                }
            )

        return candidates

    async def _attach_content_lengths(self, candidates: list[dict]) -> list[dict]:
        enriched = []
        for candidate in candidates:
            length = await self.document_downloader.head_content_length(
                candidate["url"]
            )
            candidate_copy = {**candidate, "content_length": length}
            enriched.append(candidate_copy)
        return enriched

    def _size_sort_key(self, candidate: dict) -> tuple:
        length = candidate["content_length"]
        unknown_size = length is None
        safe_length = length if length is not None else 10**12
        return (unknown_size, safe_length, candidate["titulo"])

    def _select_candidates(
        self, candidates: list[dict], options: BulkUrlSampleOptionsAppInputDTO
    ) -> list[dict]:
        if not candidates:
            return []

        max_leyes = min(options.max_leyes, len(candidates))
        if max_leyes <= 0:
            return []

        if options.modo == "limited":
            ordered = sorted(candidates, key=lambda c: c["titulo"])
            return ordered[:max_leyes]

        if options.modo == "lightweight":
            ordered = sorted(candidates, key=self._size_sort_key)
            return ordered[:max_leyes]

        randomizer = random.Random(options.seed)
        buckets = defaultdict(list)
        for candidate in candidates:
            buckets[candidate["materia_principal"]].append(candidate)

        for materia in buckets:
            buckets[materia].sort(key=self._size_sort_key)

        materias = sorted(buckets.keys())
        randomizer.shuffle(materias)

        selected = []
        while len(selected) < max_leyes and materias:
            next_materias = []
            for materia in materias:
                bucket = buckets[materia]
                if not bucket:
                    continue
                selected.append(bucket.pop(0))
                if len(selected) >= max_leyes:
                    break
                if bucket:
                    next_materias.append(materia)
            materias = next_materias

        return selected

    def _materia_distribution(self, candidates: list[dict]) -> dict[str, int]:
        counts = defaultdict(int)
        for candidate in candidates:
            counts[candidate["materia_principal"]] += 1
        return dict(sorted(counts.items(), key=lambda item: item[0]))
