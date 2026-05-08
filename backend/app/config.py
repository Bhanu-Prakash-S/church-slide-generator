from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent / "assets"

# Canvas
SLIDE_W = 1920
SLIDE_H = 1080

# Background — falls back to generated gradient if file is missing
BACKGROUND_PATH = ASSETS_DIR / "background.png"
BG_COLOR_TOP = (115, 25, 35)
BG_COLOR_BOTTOM = (75, 15, 22)

# Font
FONT_PATH = ASSETS_DIR / "fonts" / "Poppins-Bold.ttf"
MAX_FONT_SIZE = 100
MIN_FONT_SIZE = 60

# Text rendering
TEXT_COLOR = (255, 255, 255)
STROKE_COLOR = (0, 0, 0)
STROKE_WIDTH = 6
LINE_SPACING = 1.35

# Safe text area (centered inside the 1920x1080 frame)
TEXT_BOX_W = 1600
TEXT_BOX_H = 700

LINES_PER_SLIDE = 4
