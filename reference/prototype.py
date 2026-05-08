"""
Church song slide generator.
Takes section-marked lyrics + performance order and produces a styled PDF.
"""

import re
import io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import img2pdf

# ---------- Style configuration ----------
SLIDE_W, SLIDE_H = 1920, 1080
BG_COLOR_TOP = (115, 25, 35)      # dark red
BG_COLOR_BOTTOM = (75, 15, 22)    # darker red for subtle gradient
TEXT_COLOR = (255, 255, 255)
STROKE_COLOR = (0, 0, 0)
STROKE_WIDTH = 6
FONT_PATH = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"

# Font sizing — auto-shrink within these bounds
MAX_FONT_SIZE = 100
MIN_FONT_SIZE = 60
LINE_SPACING = 1.35  # multiplier on font size

# Text box (with safe margins inside the 1920x1080 frame)
TEXT_BOX_W = 1600
TEXT_BOX_H = 700

# How many lines per slide (target)
LINES_PER_SLIDE = 4


def make_background():
    """Create the dark red background with subtle vertical streak texture."""
    img = Image.new("RGB", (SLIDE_W, SLIDE_H), BG_COLOR_TOP)
    pixels = img.load()
    # Subtle vertical gradient
    for y in range(SLIDE_H):
        t = y / SLIDE_H
        r = int(BG_COLOR_TOP[0] * (1 - t) + BG_COLOR_BOTTOM[0] * t)
        g = int(BG_COLOR_TOP[1] * (1 - t) + BG_COLOR_BOTTOM[1] * t)
        b = int(BG_COLOR_TOP[2] * (1 - t) + BG_COLOR_BOTTOM[2] * t)
        for x in range(SLIDE_W):
            pixels[x, y] = (r, g, b)

    # Add subtle vertical streaks for that "curtain" feel
    import random
    rng = random.Random(42)
    streak_layer = Image.new("RGBA", (SLIDE_W, SLIDE_H), (0, 0, 0, 0))
    streak_draw = ImageDraw.Draw(streak_layer)
    for _ in range(180):
        x = rng.randint(0, SLIDE_W)
        alpha = rng.randint(8, 22)
        # darker streak
        streak_draw.line([(x, 0), (x, SLIDE_H)], fill=(0, 0, 0, alpha), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), streak_layer).convert("RGB")
    return img


def measure_text_block(lines, font, draw):
    """Return (width, height) of a multi-line text block."""
    if not lines:
        return 0, 0
    line_h = int(font.size * LINE_SPACING)
    max_w = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=STROKE_WIDTH)
        w = bbox[2] - bbox[0]
        if w > max_w:
            max_w = w
    total_h = line_h * len(lines) - int(font.size * (LINE_SPACING - 1))
    return max_w, total_h


def fit_font_size(lines, draw, max_w, max_h):
    """Find the largest font size where the lines fit within the text box."""
    for size in range(MAX_FONT_SIZE, MIN_FONT_SIZE - 1, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        w, h = measure_text_block(lines, font, draw)
        if w <= max_w and h <= max_h:
            return font
    return ImageFont.truetype(FONT_PATH, MIN_FONT_SIZE)


def render_slide(lines, bg_template):
    """Render a single slide with the given lines of text."""
    img = bg_template.copy()
    draw = ImageDraw.Draw(img)
    font = fit_font_size(lines, draw, TEXT_BOX_W, TEXT_BOX_H)

    line_h = int(font.size * LINE_SPACING)
    total_h = line_h * len(lines) - int(font.size * (LINE_SPACING - 1))
    y = (SLIDE_H - total_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=STROKE_WIDTH)
        line_w = bbox[2] - bbox[0]
        x = (SLIDE_W - line_w) // 2 - bbox[0]
        # Adjust y for stroke offset
        draw.text(
            (x, y - bbox[1]),
            line,
            font=font,
            fill=TEXT_COLOR,
            stroke_width=STROKE_WIDTH,
            stroke_fill=STROKE_COLOR,
        )
        y += line_h

    return img


# ---------- Lyrics parsing ----------

SECTION_PATTERN = re.compile(r"^\s*\[([^\]]+)\]\s*$", re.MULTILINE)


def parse_sections(lyrics_text):
    """
    Parse lyrics like:
        [Verse 1]
        line 1
        line 2

        [Chorus]
        line 1
        ...
    Returns dict of {section_key: [list of non-empty lines]}.
    Section keys are normalized: "Verse 1" -> "V1", "Chorus" -> "C", "Bridge" -> "B"
    """
    parts = re.split(SECTION_PATTERN, lyrics_text)
    # parts = ['', 'Verse 1', '...content...', 'Chorus', '...', ...]
    result = {}
    for i in range(1, len(parts), 2):
        name = parts[i].strip()
        content = parts[i + 1].strip()
        key = normalize_section_key(name)
        lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
        result[key] = lines
    return result


def normalize_section_key(name):
    """Convert 'Verse 1' -> 'V1', 'Chorus' -> 'C', 'Bridge' -> 'B', etc."""
    n = name.strip().lower()
    # Pull number if present
    m = re.search(r"(\d+)", n)
    num = m.group(1) if m else ""
    if "verse" in n:
        return f"V{num}" if num else "V"
    if "chorus" in n or "refrain" in n:
        return f"C{num}" if num else "C"
    if "bridge" in n:
        return f"B{num}" if num else "B"
    if "pre" in n and "chorus" in n:
        return f"PC{num}" if num else "PC"
    if "outro" in n or "ending" in n:
        return "O"
    if "intro" in n:
        return "I"
    # fallback: uppercase first letter + number
    return name.strip().upper().replace(" ", "")


def parse_order(order_str):
    """Parse 'V1, C, V2, C, C, B, C' into ['V1', 'C', 'V2', 'C', 'C', 'B', 'C']."""
    return [tok.strip().upper() for tok in order_str.split(",") if tok.strip()]


# ---------- Slide chunking ----------

def chunk_section_into_slides(lines, lines_per_slide=LINES_PER_SLIDE):
    """
    Split a list of lyric lines into slides of ~N lines each.
    Tries to keep natural pairs together by chunking on multiples of 2.
    """
    if not lines:
        return []
    # If the section is short, one slide
    if len(lines) <= lines_per_slide:
        return [lines]
    # Otherwise chunk into groups, preferring even splits
    chunks = []
    for i in range(0, len(lines), lines_per_slide):
        chunks.append(lines[i : i + lines_per_slide])
    # If last chunk is just 1 line and previous chunk has room, merge or rebalance
    if len(chunks) >= 2 and len(chunks[-1]) == 1 and len(chunks[-2]) >= 3:
        # move one line from previous to last to make 3+2 instead of 4+1
        chunks[-1].insert(0, chunks[-2].pop())
    return chunks


# ---------- Main pipeline ----------

def generate_slides(lyrics_text, order_str):
    """Top-level: parse lyrics + order, return list of slide images."""
    sections = parse_sections(lyrics_text)
    order = parse_order(order_str)

    # Pre-compute slide chunks for each section
    section_slides = {key: chunk_section_into_slides(lines) for key, lines in sections.items()}

    bg_template = make_background()

    all_images = []
    for section_key in order:
        if section_key not in section_slides:
            print(f"  WARNING: section '{section_key}' not found in lyrics. Skipping.")
            continue
        for chunk in section_slides[section_key]:
            img = render_slide(chunk, bg_template)
            all_images.append(img)

    return all_images


def save_as_pdf(images, output_path):
    """Convert list of PIL images to a single PDF using img2pdf for tight file sizes."""
    img_bytes_list = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        img_bytes_list.append(buf.getvalue())

    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(img_bytes_list))

    return output_path


# ---------- Demo run with "Because He Lives" ----------

if __name__ == "__main__":
    LYRICS = """[Verse 1]
God sent His Son,
They called Him, Jesus
He came to love,
Heal and forgive;
He lived and died
To buy my pardon,
An empty grave is there
To prove my Savior lives!

[Chorus]
Because He lives,
I can face tomorrow!
Because He lives,
All fear is gone
Because I know
He holds the future,
And life is worth the living,
Just because He lives!

[Verse 2]
How sweet to hold
A newborn baby,
And feel the pride
And joy he brings
But greater still
The calm assurance
This child can face
Uncertain days because He Lives!

[Verse 3]
And then one day,
I'll cross the river,
I'll fight life's final
War with pain
And then, as death
Gives way to victory,
I'll see the lights of glory
And I'll know He lives!
"""

    ORDER = "V1, C, V2, C, V3, C"

    print("Generating slides...")
    images = generate_slides(LYRICS, ORDER)
    print(f"Rendered {len(images)} slides")

    out_path = "/home/claude/because_he_lives_test.pdf"
    save_as_pdf(images, out_path)
    size_kb = Path(out_path).stat().st_size / 1024
    print(f"Saved PDF: {out_path} ({size_kb:.1f} KB)")

    # Also save first slide as preview image
    images[0].save("/home/claude/preview_slide_1.png")
    images[1].save("/home/claude/preview_slide_2.png") if len(images) > 1 else None
