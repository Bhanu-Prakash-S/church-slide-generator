"""
CLI entry point.

Usage:
    uv run python -m app --input lyrics.txt --order "V1,C,V2,C" --out slides.pdf
"""

import argparse
from pathlib import Path

from app.parsing import parse_sections, parse_order
from app.slides import generate_pdf


def main():
    parser = argparse.ArgumentParser(description="Generate church song slides as PDF")
    parser.add_argument("--input", required=True, help="Path to lyrics file with section markers")
    parser.add_argument("--order", required=True, help='Performance order e.g. "V1,C,V2,C"')
    parser.add_argument("--out", default="slides.pdf", help="Output PDF path (default: slides.pdf)")
    args = parser.parse_args()

    lyrics_text = Path(args.input).read_text(encoding="utf-8")
    sections = parse_sections(lyrics_text)
    order = parse_order(args.order)

    print(f"Sections found: {list(sections.keys())}")
    print(f"Order: {order}")

    out_path = generate_pdf(sections, order, Path(args.out))
    size_kb = out_path.stat().st_size / 1024
    print(f"PDF saved: {out_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
