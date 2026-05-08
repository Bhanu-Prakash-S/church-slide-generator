"""
Core slide engine: chunking, rendering, and PDF assembly.
"""

import io
import random
from pathlib import Path

import img2pdf
from PIL import Image, ImageDraw, ImageFont

from app import config


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


# ---------- Text layout ----------

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
    # Total height: N line-heights minus the extra spacing on the last line
    total_h = line_h * len(lines) - int(font.size * (config.LINE_SPACING - 1))
    return max_w, total_h


def _fit_font(
    lines: list[str], draw: ImageDraw.ImageDraw
) -> ImageFont.FreeTypeFont:
    """Largest font size (within bounds) where all lines fit in the text box."""
    font_path = str(config.FONT_PATH)
    for size in range(config.MAX_FONT_SIZE, config.MIN_FONT_SIZE - 1, -2):
        font = ImageFont.truetype(font_path, size)
        w, h = _measure_text_block(lines, font, draw)
        if w <= config.TEXT_BOX_W and h <= config.TEXT_BOX_H:
            return font
    return ImageFont.truetype(font_path, config.MIN_FONT_SIZE)


# ---------- Slide rendering ----------

def render_slide(lines: list[str], bg: Image.Image) -> Image.Image:
    """Render one slide: copy bg, center the text block, return the image."""
    img = bg.copy()
    draw = ImageDraw.Draw(img)
    font = _fit_font(lines, draw)

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
    Split a section's lines into slide-sized chunks.
    Rebalances the last chunk if it would be a single orphaned line (4+1 -> 3+2).
    """
    if not lines:
        return []
    if len(lines) <= lines_per_slide:
        return [lines]

    chunks = [lines[i : i + lines_per_slide] for i in range(0, len(lines), lines_per_slide)]

    if len(chunks) >= 2 and len(chunks[-1]) == 1 and len(chunks[-2]) >= 3:
        chunks[-1].insert(0, chunks[-2].pop())

    return chunks


# ---------- PDF assembly ----------

def generate_pdf(
    sections: dict[str, list[str]],
    order: list[str],
    output_path: Path,
) -> Path:
    """
    Render all slides for the given order and write a PDF to output_path.
    Skips (with a warning) any order entry whose section key isn't in sections.
    Returns the output path.
    """
    if not config.FONT_PATH.exists():
        raise FileNotFoundError(
            f"Font not found: {config.FONT_PATH}\n"
            "Place Poppins-Bold.ttf in backend/assets/fonts/"
        )

    bg = load_background()
    section_chunks = {key: chunk_section(lines) for key, lines in sections.items()}

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
