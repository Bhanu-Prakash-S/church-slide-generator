from pathlib import Path
from app.parsing import normalize_section_key, parse_sections, parse_order, effective_word_count

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


def test_effective_word_count_all_long():
    # "He"(2 letters) and "I"(1 letter) are short -> 2 short = 1; long: Because,lives,can,face,tomorrow=5 -> total=6
    assert effective_word_count("Because He lives I can face tomorrow") == 6

def test_effective_word_count_short_pairs():
    # "I am so in" = 4 short words -> ceil(4/2)=2; "love with the Lord" = 4 long -> 6
    assert effective_word_count("I am so in love with the Lord") == 6

def test_effective_word_count_odd_shorts():
    # "I am in" = 3 short -> ceil(3/2)=2; "the arms of my God" -> "the"=3 long, "arms"=long, "of"=short,"my"=short -> 2 long + 1 short pair = 3; total = 2+3=5
    # Actually: I(short), am(short), in(short), the(long), arms(long), of(short), my(short), God(long)
    # short: I, am, in, of, my = 5 -> ceil(5/2)=3; long: the, arms, God = 3 -> total=6
    assert effective_word_count("I am in the arms of my God") == 6

def test_effective_word_count_punctuation_stripped():
    # "He," -> "He" -> 2 letters -> short
    assert effective_word_count("He, came to love and heal the world") == 7
