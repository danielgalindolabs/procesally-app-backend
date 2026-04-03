import argparse
import csv
import html
import json
import random
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


ARTICLE_NUM_PATTERN = re.compile(
    r"^ARTICULO\s+([0-9]+(?:\s*(?:BIS|TER|QUATER|QUINQUIES))?[A-Z0-9ºO]*)"
)
ARTICLE_WORD_PATTERN = re.compile(
    r"^ARTICULO\s+(UNICO|PRIMERO|SEGUNDO|TERCERO|CUARTO|QUINTO|SEXTO|SEPTIMO|OCTAVO|NOVENO|DECIMO)\b"
)
TRANSITORY_PATTERN = re.compile(r"^TRANSITORIOS?$")
ROMAN_FRACTION_PATTERN = re.compile(r"^[IVXLCDM]+\.")
BOOK_PATTERN = re.compile(r"^LIBRO\b")
TITLE_PATTERN = re.compile(r"^TITULO\b")
CHAPTER_PATTERN = re.compile(r"^CAPITULO\b")


@dataclass
class ArticleHit:
    paragraph_index: int
    header_text: str
    article_number: str
    numeric_base: Optional[int]
    in_transitory: bool


def canonical(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.replace("\xa0", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip().upper()
    return normalized


def extract_paragraphs(content: str) -> List[str]:
    chunks = re.findall(r"<p>(.*?)</p>", content, flags=re.DOTALL | re.IGNORECASE)

    if not chunks:
        chunks = re.findall(r"<li>(.*?)</li>", content, flags=re.DOTALL | re.IGNORECASE)

    paragraphs = []
    for chunk in chunks:
        text = re.sub(r"<[^>]+>", " ", chunk)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            paragraphs.append(text)

    return paragraphs


def parse_article_hits(paragraphs: List[str]) -> List[ArticleHit]:
    hits: List[ArticleHit] = []
    in_transitory = False

    for idx, paragraph in enumerate(paragraphs):
        canon = canonical(paragraph)

        if TRANSITORY_PATTERN.match(canon):
            in_transitory = True
            continue

        num_match = ARTICLE_NUM_PATTERN.match(canon)
        word_match = ARTICLE_WORD_PATTERN.match(canon)

        if num_match:
            article_number = num_match.group(1).replace("º", "").strip()
            num_base_match = re.match(r"^(\d+)", article_number)
            numeric_base = int(num_base_match.group(1)) if num_base_match else None
            hits.append(
                ArticleHit(
                    paragraph_index=idx,
                    header_text=paragraph,
                    article_number=article_number,
                    numeric_base=numeric_base,
                    in_transitory=in_transitory,
                )
            )
            continue

        if word_match:
            hits.append(
                ArticleHit(
                    paragraph_index=idx,
                    header_text=paragraph,
                    article_number=word_match.group(1),
                    numeric_base=None,
                    in_transitory=in_transitory,
                )
            )

    return hits


def detect_reset_count(hits: List[ArticleHit]) -> int:
    numeric = [h.numeric_base for h in hits if h.numeric_base is not None]
    resets = 0
    for i in range(1, len(numeric)):
        if numeric[i] < numeric[i - 1]:
            resets += 1
    return resets


def sample_indices(total: int, wanted: int) -> List[int]:
    if total <= wanted:
        return list(range(total))
    if wanted <= 1:
        return [0]

    last = total - 1
    out = []
    seen = set()
    for i in range(wanted):
        idx = round((i * last) / (wanted - 1))
        if idx not in seen:
            out.append(idx)
            seen.add(idx)
    return sorted(out)


def article_bucket(article_headers_total: int) -> str:
    if article_headers_total <= 20:
        return "tiny"
    if article_headers_total <= 80:
        return "small"
    if article_headers_total <= 250:
        return "medium"
    return "large"


def size_bucket(char_count: int) -> str:
    if char_count < 120_000:
        return "short"
    if char_count < 500_000:
        return "mid"
    return "long"


def build_dataset(
    laws_dir: Path,
    output_dir: Path,
    windows_per_file: int,
    sample_files_target: int,
    seed: int,
) -> Dict[str, int]:
    files = sorted(laws_dir.glob("*.html"))
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = output_dir / "corpus_manifest.jsonl"
    windows_path = output_dir / "article_boundary_windows.jsonl"
    anomalies_path = output_dir / "anomalies.csv"
    sample_index_path = output_dir / "stratified_sample_index.json"

    anomalies_rows = []
    all_manifest_rows = []
    all_windows = []

    for file_path in files:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        paragraphs = extract_paragraphs(content)
        hits = parse_article_hits(paragraphs)

        article_headers_total = len(hits)
        article_numeric_count = sum(1 for h in hits if h.numeric_base is not None)
        article_word_count = article_headers_total - article_numeric_count
        transitorios_count = sum(
            1 for p in paragraphs if TRANSITORY_PATTERN.match(canonical(p))
        )
        roman_fraction_lines = sum(
            1 for p in paragraphs if ROMAN_FRACTION_PATTERN.match(canonical(p))
        )

        article_number_counts: Dict[str, int] = {}
        for hit in hits:
            key = hit.article_number
            article_number_counts[key] = article_number_counts.get(key, 0) + 1

        duplicated_numbers = sum(1 for v in article_number_counts.values() if v > 1)
        duplicate_article_number_rate = (
            duplicated_numbers / article_headers_total if article_headers_total else 0.0
        )
        article_reset_count = detect_reset_count(hits)

        row = {
            "file": file_path.name,
            "chars": len(content),
            "paragraphs": len(paragraphs),
            "article_headers_total": article_headers_total,
            "article_numeric_count": article_numeric_count,
            "article_word_count": article_word_count,
            "transitorios_count": transitorios_count,
            "roman_fraction_lines": roman_fraction_lines,
            "duplicate_article_number_rate": round(duplicate_article_number_rate, 6),
            "article_reset_count": article_reset_count,
            "article_bucket": article_bucket(article_headers_total),
            "size_bucket": size_bucket(len(content)),
        }
        all_manifest_rows.append(row)

        issues = []
        if article_headers_total == 0:
            issues.append("no_article_headers")
        if duplicate_article_number_rate > 0.15:
            issues.append("high_duplicate_rate")
        if article_reset_count > 0:
            issues.append("article_resets")
        if transitorios_count > 0 and article_headers_total > 0:
            ratio = transitorios_count / max(1, article_headers_total)
            if ratio > 0.4:
                issues.append("high_transitorios_ratio")

        if issues:
            anomalies_rows.append(
                {
                    "file": file_path.name,
                    "issues": "|".join(issues),
                    "article_headers_total": article_headers_total,
                    "duplicate_article_number_rate": round(
                        duplicate_article_number_rate, 6
                    ),
                    "article_reset_count": article_reset_count,
                    "transitorios_count": transitorios_count,
                }
            )

        if hits:
            sampled_hits = sample_indices(len(hits), windows_per_file)
            for idx in sampled_hits:
                hit = hits[idx]
                p_idx = hit.paragraph_index
                before = paragraphs[max(0, p_idx - 3) : p_idx]
                after = paragraphs[p_idx + 1 : p_idx + 4]
                all_windows.append(
                    {
                        "file": file_path.name,
                        "article_number": hit.article_number,
                        "paragraph_index": p_idx,
                        "in_transitory": hit.in_transitory,
                        "before": before,
                        "header": paragraphs[p_idx],
                        "after": after,
                    }
                )

    with manifest_path.open("w", encoding="utf-8") as f:
        for row in all_manifest_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with windows_path.open("w", encoding="utf-8") as f:
        for row in all_windows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with anomalies_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file",
                "issues",
                "article_headers_total",
                "duplicate_article_number_rate",
                "article_reset_count",
                "transitorios_count",
            ],
        )
        writer.writeheader()
        writer.writerows(anomalies_rows)

    rng = random.Random(seed)
    buckets: Dict[str, List[dict]] = {}
    for row in all_manifest_rows:
        key = f"{row['article_bucket']}::{row['size_bucket']}"
        buckets.setdefault(key, []).append(row)

    for key in buckets:
        buckets[key].sort(key=lambda x: x["file"])
        rng.shuffle(buckets[key])

    sample_files = []
    ordered_bucket_keys = sorted(buckets.keys())
    while len(sample_files) < sample_files_target and ordered_bucket_keys:
        next_round = []
        for key in ordered_bucket_keys:
            if not buckets[key]:
                continue
            sample_files.append(buckets[key].pop())
            if len(sample_files) >= sample_files_target:
                break
            if buckets[key]:
                next_round.append(key)
        ordered_bucket_keys = next_round

    sample_payload = {
        "seed": seed,
        "target": sample_files_target,
        "selected": len(sample_files),
        "files": [r["file"] for r in sample_files],
        "details": sample_files,
    }
    sample_index_path.write_text(
        json.dumps(sample_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return {
        "files": len(all_manifest_rows),
        "windows": len(all_windows),
        "anomalies": len(anomalies_rows),
        "sample_files": len(sample_files),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera dataset compacto para iterar parser legal sin leer todo el corpus"
    )
    parser.add_argument("--laws-dir", default="leyes")
    parser.add_argument("--output-dir", default="leyes/analysis")
    parser.add_argument("--windows-per-file", type=int, default=40)
    parser.add_argument("--sample-files-target", type=int, default=60)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    stats = build_dataset(
        laws_dir=Path(args.laws_dir),
        output_dir=Path(args.output_dir),
        windows_per_file=args.windows_per_file,
        sample_files_target=args.sample_files_target,
        seed=args.seed,
    )

    print(json.dumps({"ok": True, **stats}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
