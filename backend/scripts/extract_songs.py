"""
One-time extraction script: reads English songs from assets/Songs Book.pdf
and writes backend/assets/songs_db.json.

Run from repo root:
    python backend/scripts/extract_songs.py

Requires pdfplumber:
    pip install pdfplumber
"""

import json
import re
import sys
from pathlib import Path

import pdfplumber

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent.parent
PDF_PATH  = REPO_ROOT / "assets" / "Songs Book.pdf"
OUT_PATH  = REPO_ROOT / "backend" / "assets" / "songs_db.json"

# English songs span pages 230–430 (0-indexed). Telugu songs appear before
# ~page 235 and again after ~page 417; the ASCII-uppercase title filter
# blocks them without needing exact page boundaries.
START_PAGE          = 233  # page 234: "HYMNS / 1. The King is coming"
END_PAGE            = 418  # pages 418+ are the tail Telugu section (garbled)
CONTEMPORARY_START  = 356  # page 357: contemporary worship section begins here.
                           # Traditional hymns use 10-12px line gaps, 18-20px stanza gaps.
                           # Contemporary songs use 10-18px line gaps, 22-30px stanza gaps.

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
GAP_TRADITIONAL   = 16   # threshold for traditional hymns section
GAP_CONTEMPORARY  = 21   # threshold for contemporary worship section

# Require ASCII-uppercase title start so Telugu titles are rejected.
SONG_RE    = re.compile(r"^(\d+)\s*\.\s*([A-Z][A-Za-z\s,'\-\(\)!?]+)")
CHORUS_RE  = re.compile(r"^Chorus\s*[:.]\s*(.*)", re.IGNORECASE)
BRIDGE_RE  = re.compile(r"^Bridge\s*:\s*(.*)",  re.IGNORECASE)
REFRAIN_RE = re.compile(r"^Refrain\s*:\s*(.*)", re.IGNORECASE)
CHO_RE     = re.compile(r"^Cho\.?\s*$",          re.IGNORECASE)
PAGE_NUM_RE= re.compile(r"^\d{2,3}$")

# ---------------------------------------------------------------------------
# Step 1 – extract lines with paragraph-break flags using y-coordinates
# ---------------------------------------------------------------------------

def extract_lines(pdf: pdfplumber.PDF) -> list[tuple[str, bool, int]]:
    """
    Returns list of (text, is_paragraph_break_before, page_number).
    Paragraph break = gap between consecutive lines >= GAP_THRESHOLD px.
    Page transitions reset the y tracker so they never trigger a false break.
    """
    result: list[tuple[str, bool, int]] = []
    prev_y: int | None = None

    for page_idx in range(START_PAGE, END_PAGE):
        gap_threshold = (
            GAP_CONTEMPORARY if page_idx >= CONTEMPORARY_START else GAP_TRADITIONAL
        )
        page = pdf.pages[page_idx]
        words = page.extract_words()
        if not words:
            continue

        lines_by_y: dict[int, list[str]] = {}
        for w in words:
            y = round(w["top"] / 2) * 2
            lines_by_y.setdefault(y, []).append(w["text"])

        for y in sorted(lines_by_y):
            text = " ".join(lines_by_y[y]).strip()
            if PAGE_NUM_RE.match(text):
                continue  # skip standalone page numbers

            # Negative gap means we crossed a page boundary — not a break.
            is_break = (
                prev_y is not None and (y - prev_y) >= gap_threshold
            )
            result.append((text, is_break, page_idx + 1))
            prev_y = y

        # Reset between pages so first line of next page is never a false break.
        prev_y = None

    return result


# ---------------------------------------------------------------------------
# Step 2 – smart verse split
# ---------------------------------------------------------------------------

def smart_split(sections: dict) -> dict:
    """
    Split any verse whose length is an exact multiple of the shortest verse
    AND at least twice as long — these are page-boundary merges.
    Leaves songs where ALL verses are the same length (genuine long stanzas)
    untouched.
    """
    verse_keys = [k for k in sections if k.startswith("V")]
    if len(verse_keys) < 2:
        return sections

    lengths = [len(sections[k]) for k in verse_keys]
    typical = min(lengths)
    if typical == 0:
        return sections

    # If every verse is the same length there's nothing to split.
    if all(ln == lengths[0] for ln in lengths):
        return sections

    result: dict = {}
    verse_counter = 0
    for key in list(sections.keys()):
        val = sections[key]
        if (
            key.startswith("V")
            and len(val) >= typical * 2
            and len(val) % typical == 0
        ):
            for chunk_start in range(0, len(val), typical):
                verse_counter += 1
                result[f"V{verse_counter}"] = val[chunk_start : chunk_start + typical]
        elif key.startswith("V"):
            verse_counter += 1
            result[f"V{verse_counter}"] = val
        else:
            result[key] = val  # C, B unchanged
    return result


# ---------------------------------------------------------------------------
# Step 3 – parse songs from extracted lines
# ---------------------------------------------------------------------------

def parse_songs(lines: list[tuple[str, bool, int]]) -> list[dict]:
    songs: list[dict] = []
    current: dict | None = None
    section_lines: list[str] = []
    verse_count = 0
    section_type = "V"  # current section: 'V', 'C', 'B'
    current_page = 0

    def flush() -> None:
        nonlocal section_lines, verse_count
        clean = [ln for ln in section_lines if ln.strip()]
        if not clean or current is None:
            section_lines.clear()
            return
        if section_type == "C":
            current["sections"]["C"] = clean
        elif section_type == "B":
            current["sections"]["B"] = clean
        else:
            verse_count += 1
            current["sections"][f"V{verse_count}"] = clean
        section_lines.clear()

    def start_section(stype: str, inline: str = "") -> None:
        nonlocal section_type
        flush()
        section_type = stype
        if inline:
            section_lines.append(inline)

    for text, is_break, page_num in lines:
        song_m    = SONG_RE.match(text)
        chorus_m  = CHORUS_RE.match(text)
        bridge_m  = BRIDGE_RE.match(text)
        refrain_m = REFRAIN_RE.match(text)
        cho_trunc = CHO_RE.match(text)

        if song_m:
            flush()
            if current:
                current["sections"] = smart_split(current["sections"])
                songs.append(current)
            current = {
                "number":   int(song_m.group(1)),
                "title":    song_m.group(2).strip().rstrip("."),
                "title_normalized": song_m.group(2).strip().rstrip(".").lower(),
                "sections": {},
                "source":   "book",
                "page":     page_num,
            }
            verse_count = 0
            section_type = "V"
            section_lines.clear()

        elif chorus_m or refrain_m or cho_trunc:
            m = chorus_m or refrain_m
            inline = m.group(1).strip() if m else ""
            start_section("C", inline)

        elif bridge_m:
            start_section("B", bridge_m.group(1).strip())

        elif is_break:
            flush()
            section_type = "V"
            section_lines.append(text)

        else:
            if current is not None:
                section_lines.append(text)

    flush()
    if current:
        current["sections"] = smart_split(current["sections"])
        songs.append(current)

    return songs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"Reading {PDF_PATH} ...")
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"  Total PDF pages: {len(pdf.pages)}")
        lines = extract_lines(pdf)
        print(f"  Lines extracted: {len(lines)}")
        songs = parse_songs(lines)

    print(f"  Songs parsed:    {len(songs)}")

    # Warn about songs with no sections (likely extraction failures)
    empty = [s for s in songs if not s["sections"]]
    if empty:
        print(f"  WARNING: {len(empty)} songs have no sections:")
        for s in empty:
            print(f"    #{s['number']} '{s['title']}' (p{s['page']})")

    # Warn about very large single sections (possible undetected merges)
    large = [
        s for s in songs
        if any(len(v) > 10 for v in s["sections"].values())
    ]
    if large:
        print(f"  WARNING: {len(large)} songs have a section with >10 lines (may need review):")
        for s in large:
            for k, v in s["sections"].items():
                if len(v) > 10:
                    print(f"    #{s['number']} '{s['title']}' {k}={len(v)} lines (p{s['page']})")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)

    print(f"\nWrote {len(songs)} songs -> {OUT_PATH}")


if __name__ == "__main__":
    main()
