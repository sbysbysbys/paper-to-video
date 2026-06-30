#!/usr/bin/env python3
import argparse
import csv
import json
import re
from pathlib import Path


def fail(message):
    raise SystemExit(f"error: {message}")


def clean_text(value):
    return re.sub(r"\s+", " ", value or "").strip()


def caption_candidates(page_text):
    patterns = [
        r"(Figure|Fig\.?)\s+\d+[:.\s].{0,500}",
        r"(Table)\s+\d+[:.\s].{0,500}",
    ]
    found = []
    for pattern in patterns:
        for match in re.finditer(pattern, page_text, flags=re.IGNORECASE):
            found.append(clean_text(match.group(0)))
    return found


def extract_with_pymupdf(pdf_path, out_dir):
    try:
        import fitz
    except ImportError:
        return None

    doc = fitz.open(pdf_path)
    figures_dir = out_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    pages = []
    assets = {"figures": [], "tables": [], "equations": []}
    paper_text_parts = []

    for page_index, page in enumerate(doc, start=1):
        text = page.get_text("text")
        paper_text_parts.append(f"\n\n--- Page {page_index} ---\n{text}")
        captions = caption_candidates(text)
        image_infos = page.get_images(full=True)
        page_figures = []

        for image_index, image_info in enumerate(image_infos, start=1):
            xref = image_info[0]
            try:
                image = doc.extract_image(xref)
            except Exception:
                continue
            ext = image.get("ext") or "png"
            image_path = figures_dir / f"page_{page_index:03d}_figure_{image_index:02d}.{ext}"
            image_path.write_bytes(image["image"])
            item = {
                "id": f"fig-p{page_index:03d}-{image_index:02d}",
                "type": "figure",
                "page": page_index,
                "path": str(image_path),
                "caption_candidates": captions,
            }
            assets["figures"].append(item)
            page_figures.append(item)

        pages.append(
            {
                "page": page_index,
                "text": text,
                "caption_candidates": captions,
                "figures": page_figures,
            }
        )

    (out_dir / "paper.txt").write_text("".join(paper_text_parts).strip(), encoding="utf-8")
    return pages, assets


def extract_tables_with_pdfplumber(pdf_path, out_dir, pages, assets):
    try:
        import pdfplumber
    except ImportError:
        return

    tables_dir = out_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    with pdfplumber.open(pdf_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            try:
                tables = page.extract_tables() or []
            except Exception:
                continue
            for table_index, table in enumerate(tables, start=1):
                csv_path = tables_dir / f"page_{page_index:03d}_table_{table_index:02d}.csv"
                with csv_path.open("w", encoding="utf-8", newline="") as handle:
                    writer = csv.writer(handle)
                    writer.writerows(table)
                item = {
                    "id": f"table-p{page_index:03d}-{table_index:02d}",
                    "type": "table",
                    "page": page_index,
                    "path": str(csv_path),
                    "caption_candidates": pages[page_index - 1].get("caption_candidates", []),
                }
                assets["tables"].append(item)
                pages[page_index - 1].setdefault("tables", []).append(item)


def main():
    parser = argparse.ArgumentParser(description="Extract text, figures, and tables from a paper PDF.")
    parser.add_argument("--pdf", required=True, help="Input paper PDF.")
    parser.add_argument("--out", required=True, help="Output extraction directory.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()
    out_dir = Path(args.out).resolve()
    if not pdf_path.exists():
        fail(f"PDF not found: {pdf_path}")

    out_dir.mkdir(parents=True, exist_ok=True)
    extracted = extract_with_pymupdf(pdf_path, out_dir)
    if extracted is None:
        fail("PyMuPDF is required for PDF extraction. Install package `pymupdf` or use the pdf skill fallback.")

    pages, assets = extracted
    extract_tables_with_pdfplumber(pdf_path, out_dir, pages, assets)

    manifest = {
        "source_pdf": str(pdf_path),
        "pages_count": len(pages),
        "figures_count": len(assets["figures"]),
        "tables_count": len(assets["tables"]),
        "assets": assets,
    }
    (out_dir / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "assets_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"out": str(out_dir), "pages": len(pages), "figures": len(assets["figures"]), "tables": len(assets["tables"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
