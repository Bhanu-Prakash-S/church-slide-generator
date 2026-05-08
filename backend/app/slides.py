"""
Core slide engine: chunking, rendering, and PDF assembly.
"""

import io
import random
import re
from pathlib import Path

import img2pdf
from PIL import Image, ImageDraw, ImageFont

from app import config
from app.parsing import effective_word_count

# Reused for text measurement — no need to create a real image just to call textbbox
_DUMMY_DRAW = ImageDraw.Draw(Image.new("RGB", (1, 1)))

# Words that mark a natural phrase boundary for line splitting
_NATURAL_BREAK_WORDS = {"and", "but", "for", "when", "even", "like", "or", "so", "yet", "nor"}

# How many font sizes below MAX to try before deciding a line needs splitting
_FONT_TRIAL_STEPS = 4


# ---------- Background ----------

def _make_gradient_background() -> Image.Image:
    """Fallback gradient background when background.png is missing."""
    img = Image.new("RGB", (config.SLIDE_W, config.SLIDE_H))
    pixels = img.load()
    for y in range(config.SLIDE_H):
        t = y / config.SLIDE_H
        r = int(config.BG_COLOR_TOP[0] * (1 - t) + config.BG_COLOR_BOTTOM[0] * t)
        g = int(config.BG_COLOR_TOP[1] * (1 - t) + config.BG_COLOR_BOTTOM[1] * t)
        b = int(config.BG_COLOR_TOP[2] * (1 - t) + config.BG_COLOR_BOTTOM[2] * t)
        for x in range(config.SLIDE_W):
            pixels[x, y] = (r, g, b)

    streak_layer = Image.new("RGBA", (config.SLIDE_W, config.SLIDE_H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(streak_layer)
    rng = random.Random(42)
    for _ in range(180):
        x = rng.randint(0, config.SLIDE_W)
        alpha = rng.randint(8, 22)
        draw.line([(x, 0), (x, config.SLIDE_H)], fill=(0, 0, 0, alpha), width=1)
    return Image.alpha_composite(img.convert("RGBA"), streak_layer).convert("RGB")


def load_background() -> Image.Image:
    if config.BACKGROUND_PATH.exists():
        img = Image.open(config.BACKGROUND_PATH).convert("RGB")
        if img.size != (config.SLIDE_W, config.SLIDE_H):
            img = img.resize((config.SLIDE_W, config.SLIDE_H), Image.LANCZOS)
        return img
    return _make_gradient_background()


# ---------- Text measurement ----------

def _measure_text_block(
    lines: list[str], font: ImageFont.FreeTypeFont, draw: ImageDraw.ImageDraw
) -> tuple[int, int]:
    """Return (width, height) of a multi-line text block at the given font."""
    if not lines:
        return 0, 0
    line_h = int(font.size * config.LINE_SPACING)
    max_w = 0
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=config.STROKE_WIDTH)
        w = bbox[2] - bbox[0]
        if w > max_w:
            max_w = w
    total_h = line_h * len(lines) - int(font.size * (config.LINE_SPACING - 1))
    return max_w, total_h


def _line_pixel_width(line: str, font_size: int) -> int:
    """Pixel width of a single line at the given font size (includes stroke)."""
    font = ImageFont.truetype(str(config.FONT_PATH), font_size)
    bbox = _DUMMY_DRAW.textbbox((0, 0), line, font=font, stroke_width=config.STROKE_WIDTH)
    return bbox[2] - bbox[0]


def _fit_font(
    lines: list[str],
    draw: ImageDraw.ImageDraw,
    max_size: int = config.MAX_FONT_SIZE,
) -> ImageFont.FreeTypeFont:
    """Largest font size (within bounds) where all lines fit in the text box."""
    font_path = str(config.FONT_PATH)
    for size in range(max_size, config.MIN_FONT_SIZE - 1, -2):
        font = ImageFont.truetype(font_path, size)
        w, h = _measure_text_block(lines, font, draw)
        if w <= config.TEXT_BOX_W and h <= config.TEXT_BOX_H:
            return font
    return ImageFont.truetype(font_path, config.MIN_FONT_SIZE)


# ---------- Line expansion (long-line splitting) ----------

def _split_line(line: str) -> tuple[str, str]:
    """
    Split a line near its midpoint into two parts, first part gets more words.

    Priority order:
    1. Comma or semicolon: scan the whole line (excluding the last word), pick
       the one whose split point lands closest to mid. Requires ≥2 words on
       each side so a leading comma like "Yes, ..." doesn't cause a 1-word split.
    2. Natural-break word (and/but/for/etc.) at mid or mid+1 → split before it.
    3. Exact midpoint.
    """
    words = line.split()
    n = len(words)
    mid = -(-n // 2)  # ceil(n/2) — first half gets the extra word when n is odd

    # Priority 1: find all comma/semicolon positions (not on the last word)
    # and pick the one whose resulting split_at is closest to mid.
    punct_positions = [
        k for k in range(n - 1)
        if words[k] and words[k][-1] in (",", ";")
    ]
    if punct_positions:
        best_k = min(punct_positions, key=lambda k: abs((k + 1) - mid))
        split_at = best_k + 1
        # Require at least 2 words on each side to avoid degenerate splits
        if 1 < split_at < n - 1:
            return " ".join(words[:split_at]), " ".join(words[split_at:])

    # Priority 2: natural-break word near the midpoint
    for split_at in [mid, min(mid + 1, n - 1)]:
        word_core = re.sub(r"[^a-zA-Z]", "", words[split_at]).lower()
        if word_core in _NATURAL_BREAK_WORDS:
            return " ".join(words[:split_at]), " ".join(words[split_at:])

    # Default: exact midpoint
    return " ".join(words[:mid]), " ".join(words[mid:])


def _expand_line(line: str) -> list[str]:
    """
    If a line's effective word count exceeds 6 and it doesn't fit within the
    text box at MAX_FONT_SIZE down to MAX_FONT_SIZE - FONT_TRIAL_STEPS,
    split it. Recursively checks each half so very long lines keep splitting.
    """
    if effective_word_count(line) <= 6:
        return [line]

    # Try the line at MAX_FONT_SIZE down to MAX - FONT_TRIAL_STEPS
    min_trial = config.MAX_FONT_SIZE - _FONT_TRIAL_STEPS
    for size in range(config.MAX_FONT_SIZE, min_trial - 1, -1):
        if _line_pixel_width(line, size) <= config.TEXT_BOX_W:
            return [line]  # fits — slide-level _fit_font will pick the right size

    # Still too wide — split and check each half recursively
    first, second = _split_line(line)
    return _expand_line(first) + _expand_line(second)


def expand_long_lines(lines: list[str]) -> list[str]:
    """
    Pre-process a section's lines: any line that is too long to fit at the
    standard font size gets split into two shorter lines.
    """
    result = []
    for line in lines:
        result.extend(_expand_line(line))
    return result


# ---------- Slide rendering ----------

def render_slide(lines: list[str], bg: Image.Image) -> Image.Image:
    """Render one slide: copy bg, center the text block, return the image."""
    img = bg.copy()
    draw = ImageDraw.Draw(img)

    # Short slides (< 3 lines) get a 2px font boost so they fill more of the frame
    max_font = config.MAX_FONT_SIZE + 2 if len(lines) < 3 else config.MAX_FONT_SIZE
    font = _fit_font(lines, draw, max_size=max_font)

    line_h = int(font.size * config.LINE_SPACING)
    total_h = line_h * len(lines) - int(font.size * (config.LINE_SPACING - 1))
    y = (config.SLIDE_H - total_h) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=config.STROKE_WIDTH)
        line_w = bbox[2] - bbox[0]
        x = (config.SLIDE_W - line_w) // 2 - bbox[0]
        draw.text(
            (x, y - bbox[1]),
            line,
            font=font,
            fill=config.TEXT_COLOR,
            stroke_width=config.STROKE_WIDTH,
            stroke_fill=config.STROKE_COLOR,
        )
        y += line_h

    return img


# ---------- Chunking ----------

def chunk_section(lines: list[str], lines_per_slide: int = config.LINES_PER_SLIDE) -> list[list[str]]:
    """
    Split a section's lines into slides of 3–4 lines each.
    Rebalances the tail to avoid orphan slides:
      - last chunk has 1 line → 4+1 becomes 3+2
      - last chunk has 2 lines → 4+2 becomes 3+3
    """
    if not lines:
        return []
    if len(lines) <= lines_per_slide:
        return [lines]

    chunks = [lines[i : i + lines_per_slide] for i in range(0, len(lines), lines_per_slide)]

    if len(chunks) >= 2:
        last, prev = chunks[-1], chunks[-2]
        if len(last) == 1 and len(prev) >= 3:
            last.insert(0, prev.pop())
        elif len(last) == 2 and len(prev) >= 4:
            last.insert(0, prev.pop())

    return chunks


# ---------- PDF assembly ----------

def generate_pdf(
    sections: dict[str, list[str]],
    order: list[str],
    output_path: Path,
) -> Path:
    """
    Render all slides for the given order and write a PDF to output_path.
    Applies long-line expansion before chunking so every slide is readable.
    Skips (with a warning) any order entry whose section key isn't in sections.
    """
    if not config.FONT_PATH.exists():
        raise FileNotFoundError(
            f"Font not found: {config.FONT_PATH}\n"
            "Place Poppins-Bold.ttf in backend/assets/fonts/"
        )

    bg = load_background()

    # Expand long lines first, then chunk
    section_chunks = {
        key: chunk_section(expand_long_lines(lines))
        for key, lines in sections.items()
    }

    img_bytes: list[bytes] = []
    for key in order:
        if key not in section_chunks:
            print(f"WARNING: section '{key}' not in lyrics — skipping")
            continue
        for chunk in section_chunks[key]:
            slide = render_slide(chunk, bg)
            buf = io.BytesIO()
            slide.save(buf, format="JPEG", quality=85, optimize=True)
            img_bytes.append(buf.getvalue())

    if not img_bytes:
        raise ValueError("No slides were generated — check your order and lyrics.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(img_bytes))

    return output_path
