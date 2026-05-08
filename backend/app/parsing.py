import re

SECTION_PATTERN = re.compile(r"^\s*\[([^\]]+)\]\s*$", re.MULTILINE)


def normalize_section_key(name: str) -> str:
    """'Verse 1' -> 'V1', 'Chorus' -> 'C', 'Bridge' -> 'B', etc."""
    n = name.strip().lower()
    m = re.search(r"(\d+)", n)
    num = m.group(1) if m else ""

    if "pre" in n and "chorus" in n:
        return f"PC{num}" if num else "PC"
    if "verse" in n:
        return f"V{num}" if num else "V"
    if "chorus" in n or "refrain" in n:
        return f"C{num}" if num else "C"
    if "bridge" in n:
        return f"B{num}" if num else "B"
    if "outro" in n or "ending" in n:
        return "O"
    if "intro" in n:
        return "I"
    # fallback: strip spaces and uppercase
    return re.sub(r"\s+", "", name.strip().upper())


def parse_sections(lyrics_text: str) -> dict[str, list[str]]:
    """
    Parse section-marked lyrics into a dict of {key: [lines]}.

    Input format:
        [Verse 1]
        line one
        line two

        [Chorus]
        ...
    """
    parts = re.split(SECTION_PATTERN, lyrics_text)
    # After splitting on section headers the list looks like:
    # ['', 'Verse 1', 'line one\nline two\n', 'Chorus', '...', ...]
    result: dict[str, list[str]] = {}
    for i in range(1, len(parts), 2):
        key = normalize_section_key(parts[i].strip())
        lines = [ln.strip() for ln in parts[i + 1].split("\n") if ln.strip()]
        result[key] = lines
    return result


def parse_order(order_str: str) -> list[str]:
    """'V1, C, V2, C' -> ['V1', 'C', 'V2', 'C']"""
    return [tok.strip().upper() for tok in order_str.split(",") if tok.strip()]
