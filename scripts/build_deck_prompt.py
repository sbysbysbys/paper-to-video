#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


def trim(text, limit):
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n...[truncated]"


def main():
    parser = argparse.ArgumentParser(description="Build the LLM prompt used for paper-to-video deck generation.")
    parser.add_argument("--extracted", required=True, help="Directory created by extract_pdf.py.")
    parser.add_argument("--out", required=True, help="Prompt output text file.")
    parser.add_argument("--text-chars", type=int, default=45000, help="Maximum paper text characters to include.")
    args = parser.parse_args()

    extracted = Path(args.extracted).resolve()
    out = Path(args.out).resolve()
    paper_text = (extracted / "paper.txt").read_text(encoding="utf-8")
    manifest = json.loads((extracted / "assets_manifest.json").read_text(encoding="utf-8"))

    assets_lines = []
    for kind in ("figures", "tables"):
        for item in manifest.get("assets", {}).get(kind, []):
            captions = "; ".join(item.get("caption_candidates", [])[:3])
            assets_lines.append(
                f"- {item['id']} | {item['type']} | page {item['page']} | {item['path']} | captions: {captions}"
            )

    prompt = f"""You are creating a professional Chinese technical lecture deck from an academic paper.

Follow the paper's own structure and terminology. Do not impose a generic method template. If the paper explains its method through modules, follow that. If it explains through algorithms, follow that. If it explains through theory, definitions, or a system pipeline, follow that. Only discuss topics that are present in the paper.

Allocate substantial space to the introduction and motivation. Explain the background, problem setup, motivation, and research gap according to the paper's own presentation.

Allocate the largest or near-largest portion of the deck to the method section, but organize it according to the paper itself. Explain the method carefully and technically. Include key equations when they are central to the paper.

Keep experiments concise: usually 1 slide and at most 2 slides, unless the paper itself is primarily an empirical benchmark paper.

Use only the paper's original figures, tables, equations, and claims. Do not invent diagrams, decorative graphics, synthetic figures, or content not supported by the paper.

The deck should be about 5 content slides by default. Use a restrained academic style, text-first layout, readable typography, and clear slide titles.

Return a slide plan that includes:
- slide title
- slide objective
- concise but technical Chinese slide text
- original paper assets to place on the slide, using asset ids and paths below
- equations to include when important
- narration intent for the later voiceover script

Available extracted paper assets:
{chr(10).join(assets_lines) if assets_lines else "- No extracted figures or tables were found. Use paper text and equations only."}

Paper text:
{trim(paper_text, args.text_chars)}
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(prompt, encoding="utf-8")
    print(str(out))


if __name__ == "__main__":
    main()
