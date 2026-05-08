from pathlib import Path
from app.parsing import normalize_section_key, parse_sections, parse_order

FIXTURE = Path(__file__).parent / "fixtures" / "because_he_lives.txt"


def test_normalize_section_key():
    assert normalize_section_key("Verse 1") == "V1"
    assert normalize_section_key("verse 2") == "V2"
    assert normalize_section_key("Chorus") == "C"
    assert normalize_section_key("chorus 2") == "C2"
    assert normalize_section_key("Bridge") == "B"
    assert normalize_section_key("Pre-Chorus") == "PC"
    assert normalize_section_key("Intro") == "I"
    assert normalize_section_key("Outro") == "O"


def test_parse_sections_keys():
    lyrics = FIXTURE.read_text(encoding="utf-8")
    sections = parse_sections(lyrics)
    assert set(sections.keys()) == {"V1", "C", "V2", "V3"}


def test_parse_sections_line_counts():
    lyrics = FIXTURE.read_text(encoding="utf-8")
    sections = parse_sections(lyrics)
    assert len(sections["V1"]) == 8
    assert len(sections["C"]) == 8
    assert len(sections["V2"]) == 8
    assert len(sections["V3"]) == 8


def test_parse_order():
    assert parse_order("V1, C, V2, C, V3, C") == ["V1", "C", "V2", "C", "V3", "C"]
    assert parse_order("v1,c,v2") == ["V1", "C", "V2"]


def test_parse_order_strips_whitespace():
    result = parse_order("  V1 ,  C  ,  B  ")
    assert result == ["V1", "C", "B"]
