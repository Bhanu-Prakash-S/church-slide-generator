from pathlib import Path
import tempfile
from app.parsing import parse_sections, parse_order
from app.slides import chunk_section, expand_long_lines, _split_line, generate_pdf

FIXTURE = Path(__file__).parent / "fixtures" / "because_he_lives.txt"
ORDER_STR = "V1, C, V2, C, V3, C"


def test_chunk_section_short():
    assert chunk_section(["a", "b", "c"]) == [["a", "b", "c"]]
    assert chunk_section(["a", "b", "c", "d"]) == [["a", "b", "c", "d"]]


def test_chunk_section_rebalance_4_plus_1():
    # 5 lines: [4, 1] -> [3, 2]
    chunks = chunk_section(["a", "b", "c", "d", "e"])
    assert [len(c) for c in chunks] == [3, 2]


def test_chunk_section_rebalance_4_plus_2():
    # 6 lines: [4, 2] -> [3, 3]
    chunks = chunk_section(["a", "b", "c", "d", "e", "f"])
    assert [len(c) for c in chunks] == [3, 3]


def test_chunk_section_rebalance_10_lines():
    # 10 lines: [4, 4, 2] -> [4, 3, 3]
    chunks = chunk_section([str(i) for i in range(10)])
    assert [len(c) for c in chunks] == [4, 3, 3]


def test_chunk_section_even():
    lines = [str(i) for i in range(8)]
    chunks = chunk_section(lines)
    assert chunks == [["0", "1", "2", "3"], ["4", "5", "6", "7"]]


def test_split_line_even():
    first, second = _split_line("one two three four five six seven eight")
    assert first == "one two three four"
    assert second == "five six seven eight"


def test_split_line_odd():
    # 7 words -> 4 + 3
    first, second = _split_line("one two three four five six seven")
    assert len(first.split()) == 4
    assert len(second.split()) == 3


def test_split_line_natural_break():
    # "and" falls at position 4 (exactly mid for 8 words) — should split there
    first, second = _split_line("He came to love and heal the world")
    assert second.startswith("and")


def test_split_line_comma_at_mid_minus_1():
    # "love," at index 3 (mid-1 for 8 words) — still found by broad search
    first, second = _split_line("God sent His love, to heal and restore")
    assert first.endswith("love,")


def test_split_line_semicolon_near_mid():
    # "died;" at index 3 (mid-1 for 8 words)
    first, second = _split_line("He lived and died; to buy the pardon")
    assert first.endswith("died;")


def test_split_line_comma_takes_priority_over_natural_break():
    # "save," at index 3, "and" at index 4 — comma wins
    first, second = _split_line("He came to save, and love the world")
    assert first.endswith("save,")


def test_split_line_comma_before_midpoint():
    # "blessings," is at index 2 (mid-2 for 8 words) — the old code missed this.
    # New broad search finds it as the closest punctuation to mid.
    first, second = _split_line("Count your blessings, name them one by one;")
    assert first == "Count your blessings,"
    assert second == "name them one by one;"


def test_split_line_comma_before_midpoint_variant():
    first, second = _split_line("Count your blessings, see what God hath done;")
    assert first == "Count your blessings,"
    assert second == "see what God hath done;"


def test_split_line_leading_comma_ignored():
    # Comma on the first word → split_at=1 → rejected (< 2 words in first half)
    # Falls through to midpoint
    first, second = _split_line("Yes, because He lives and reigns forever more")
    assert len(first.split()) >= 2
    assert len(second.split()) >= 2


def test_expand_long_lines_short_line_unchanged():
    # 6 effective words — must not be split
    lines = expand_long_lines(["I am so in love with the Lord"])
    assert len(lines) == 1


def test_expand_long_lines_long_line_split():
    # A clearly long line that won't fit at MAX - 4 px
    long_line = "Blessed are those who hunger and thirst for righteousness for they will be filled"
    result = expand_long_lines([long_line])
    assert len(result) > 1
    # All parts should be shorter than the original
    for part in result:
        assert len(part) < len(long_line)


def test_expand_long_lines_preserves_short_sections():
    # Lines with ≤ 6 effective words are left alone
    lines = ["Because He lives", "I can face tomorrow"]
    assert expand_long_lines(lines) == lines


def test_slide_count_because_he_lives():
    lyrics = FIXTURE.read_text(encoding="utf-8")
    sections = parse_sections(lyrics)
    order = parse_order(ORDER_STR)
    # All lines in Because He Lives are short — no expansion expected
    total = sum(len(chunk_section(expand_long_lines(sections[k]))) for k in order)
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
        assert result.read_bytes()[:4] == b"%PDF"
