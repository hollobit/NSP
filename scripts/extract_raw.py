#!/usr/bin/env python3
"""
PDF → page-level raw JSON extractor.

Reads PDFs from `pdf/` and writes:
  - data/raw/master_plan.pages.json
  - data/raw/impl_plan.pages.json

Each JSON is a list of:
  { "page": int, "text": str, "tables": [[[cell,...],...], ...] }

No interpretation here — just faithful extraction. Downstream parsers
(src/parser/*.py) consume this.

Run:
  python scripts/extract_raw.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf"
RAW_DIR = ROOT / "data" / "raw"

SOURCES = [
    ("master_plan", "제6차 국가표준기본계획(2026-2030).pdf"),
    ("impl_plan", "2026 시행계획.pdf"),
]


def extract_pdf(pdf_path: Path) -> list[dict]:
    """Return page-level dicts with text + tables. Never mutates input."""
    pages: list[dict] = []
    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            pages.append(
                {
                    "page": idx,
                    "text": text,
                    "tables": tables,
                    "width": float(page.width),
                    "height": float(page.height),
                }
            )
    return pages


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()

    for key, filename in SOURCES:
        pdf_path = PDF_DIR / filename
        if not pdf_path.exists():
            print(f"[ERROR] missing: {pdf_path}", file=sys.stderr)
            return 1
        print(f"[extract] {filename}")
        pages = extract_pdf(pdf_path)
        out = RAW_DIR / f"{key}.pages.json"
        write_json(
            out,
            {
                "schema_version": "1.0",
                "source_file": filename,
                "page_count": len(pages),
                "generated_at": generated_at,
                "pages": pages,
            },
        )
        print(f"  → {out.relative_to(ROOT)}  ({len(pages)} pages)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
