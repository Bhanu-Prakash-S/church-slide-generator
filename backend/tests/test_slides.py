from pathlib import Path
import tempfile
from app.parsing import parse_sections, parse_order
from app.slides import chunk_section, generate_pdf

FIXTURE = Path(__file__).parent / "fixtures" / "because_he_lives.txt"
ORDER_STR = "V1, C, V2, C, V3, C"


def test_chunk_section_short():
    # Sections with <= 4 lines stay as one slide
    assert chunk_section(["a", "b", "c"]) == [["a", "b", "c"]]
    assert chunk_section(["a", "b", "c", "d"]) == [["a", "b", "c", "d"]]


def test_chunk_section_rebalance():
    # 5 lines: would be [4, 1] — should rebalance to [3, 2]
    lines = ["a", "b", "c", "d", "e"]
    chunks = chunk_section(lines)
    assert len(chunks) == 2
    assert len(chunks[0]) == 3
    assert len(chunks[1]) == 2


def test_chunk_section_even():
    # 8 lines: clean [4, 4]
    lines = [str(i) for i in range(8)]
    chunks = chunk_section(lines)
    assert chunks == [["0", "1", "2", "3"], ["4", "5", "6", "7"]]


def test_slide_count_because_he_lives():
    lyrics = FIXTURE.read_text(encoding="utf-8")
    sections = parse_sections(lyrics)
    order = parse_order(ORDER_STR)

    # Each section is 8 lines -> 2 slides. Order has 6 entries -> 12 slides.
    total = sum(len(chunk_section(sections[k])) for k in order)
    assert total == 12


def test_generate_pdf_creates_file():
    lyrics = FIXTURE.read_text(encoding="utf-8")
    sections = parse_sections(lyrics)
    order = parse_order(ORDER_STR)

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "test.pdf"
        result = generate_pdf(sections, order, out)
        assert result.exists()
        assert result.stat().st_size > 0
        # PDF magic bytes
        assert result.read_bytes()[:4] == b"%PDF"
