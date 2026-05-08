# Project Brief: Church Song Slide Generator

> **For Claude Code:** This document is the source of truth for what we're building, why, and how. Read this fully before writing any code. After reading, also read `ROADMAP.md` (milestones), `reference/prototype.py` (working baseline), and `assets/` (the background image to use). Then wait for the user's instructions.

## 1. The Problem (User Story)

The user, Bhanu, prepares song slides for his church every week. Current workflow:

1. Watches a YouTube video of the song to learn the performance order (which verses come when, how many times the chorus repeats, where the bridge goes).
2. Opens Canva, creates a presentation with a fixed template (dark red background, bold white text with black stroke).
3. Manually splits lyrics into ~4-line slides, adjusts font sizes so nothing overflows, duplicates chorus slides as needed.
4. Exports as PDF — output is 50–90 MB.
5. Uploads to iLovePDF.com to compress it down to under 2 MB.

This takes 15–30 minutes per song. He wants to automate it.

## 2. Project Scope (v1)

**Build:** A web app where the user pastes section-marked lyrics + a performance order string, and gets a styled PDF in seconds.

**Explicitly out of scope for v1** (deferred to v1.1+):
- YouTube link → automatic flow detection (audio download, transcription, chorus matching) — this was assessed and is a multi-month research problem with unreliable output. Not building it now.
- User-customizable backgrounds and fonts — fixed style for v1, customization later.
- User accounts / saved songs / history.

The v1 already replaces ~90% of the manual work because the painful parts are (a) layouting/sizing and (b) the export-then-compress dance, both of which programmatic generation eliminates entirely.

## 3. Architecture Decisions & Rationale

### 3.1 Stack
- **Backend:** Python + FastAPI. Chosen because the slide rendering uses Pillow (Python imaging) and FastAPI is the lightest way to wrap a single endpoint that streams a PDF response.
- **Frontend:** React (Vite-based, TypeScript). Single-page app, no SSR needed.
- **PDF generation:** `Pillow` for rendering each slide as an image, `img2pdf` for assembling images into a PDF without recompression. **Critical:** This produces 1–3 MB PDFs natively, eliminating the iLovePDF compression step.
- **Why not reportlab?** reportlab is great for text-flow PDFs but the styled visual-slide use case (background image + stroked text) is more naturally handled by raster rendering.
- **Why not Puppeteer/headless browser?** Heavier dependency, slower, overkill for fixed-template slides.

### 3.2 Input Format

Two inputs from the user:

**Lyrics with section markers:**
```
[Verse 1]
God sent His Son,
They called Him, Jesus
He came to love,
Heal and forgive;
...

[Chorus]
Because He lives,
I can face tomorrow!
...
```

**Performance order:**
```
V1, C, V2, C, V3, C
```

Section key normalization rules:
- `[Verse 1]` → `V1`, `[Verse 2]` → `V2`
- `[Chorus]` → `C`, `[Chorus 2]` → `C2`
- `[Bridge]` → `B`
- `[Pre-Chorus]` → `PC`
- `[Intro]` → `I`, `[Outro]` → `O`

Both case-insensitive on input.

### 3.3 Slide Generation Logic

- Each section's lyrics are auto-chunked into slides of ~4 lines each.
- If the last chunk would have only 1 line, rebalance with the previous chunk (so we get e.g. 3+2 instead of 4+1).
- Font size auto-shrinks (within bounds: 60–100px on a 1920×1080 canvas) to ensure no horizontal overflow of the text box.
- Lines are centered both horizontally and vertically.
- Text style: white fill (#FFFFFF), black stroke (6px), Poppins Bold.

### 3.4 Visual Style (Fixed for v1)

- Canvas: 1920 × 1080
- Background: Custom image at `backend/assets/background.png` (provided by user — see `assets/` folder in this handoff package). Falls back to a generated dark-red gradient if the file is missing.
- Font: Poppins Bold (bundled in `backend/assets/fonts/Poppins-Bold.ttf` — Claude Code: download from Google Fonts on setup if not present)
- Text color: white #FFFFFF
- Stroke: black, 6px width
- Line spacing: 1.35× font size
- Text box: 1600 × 700 (centered safe area)

### 3.5 API Design

Single primary endpoint:

```
POST /api/generate-slides
Content-Type: application/json

{
  "lyrics": "[Verse 1]\nGod sent His Son...",
  "order": "V1, C, V2, C, V3, C",
  "filename": "because_he_lives"  // optional
}

Response: application/pdf (streamed)
```

Validation endpoint (optional, for live preview):

```
POST /api/validate
{ "lyrics": "...", "order": "..." }

Response:
{
  "valid": true,
  "sections_found": ["V1", "C", "V2", "V3"],
  "order_parsed": ["V1", "C", "V2", "C", "V3", "C"],
  "missing_sections": [],
  "estimated_slide_count": 12
}
```

### 3.6 Frontend UX

- **Left panel (input):** Two textareas — lyrics (with section markers) and order. Helper buttons: "Insert [Verse]", "Insert [Chorus]", "Insert [Bridge]" to make markup easier.
- **Right panel (preview):** Live-rendered preview of the first slide and a count of total slides. Updates on input change (debounced 500ms).
- **Bottom:** "Generate PDF" button → downloads the file. Filename input above it.
- **Validation feedback:** If a section in the order isn't defined in lyrics (e.g., user wrote `B` in order but no `[Bridge]` section), show an inline error.

Keep it minimal. No login, no theming for v1.

## 4. Project Structure

```
church-slide-generator/
├── README.md
├── PROJECT_BRIEF.md          # this file (move here from handoff)
├── ROADMAP.md
├── .gitignore
├── backend/
│   ├── pyproject.toml         # use uv or poetry
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app
│   │   ├── slides.py          # core engine (port from reference/prototype.py)
│   │   ├── parsing.py         # lyrics + order parsing
│   │   ├── config.py          # style constants
│   │   └── schemas.py         # Pydantic models
│   ├── assets/
│   │   ├── background.png
│   │   └── fonts/
│   │       └── Poppins-Bold.ttf
│   └── tests/
│       ├── test_parsing.py
│       ├── test_slides.py
│       └── fixtures/
│           └── because_he_lives.txt
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── components/
        │   ├── LyricsInput.tsx
        │   ├── OrderInput.tsx
        │   ├── SlidePreview.tsx
        │   └── GenerateButton.tsx
        ├── api/
        │   └── client.ts
        └── styles.css
```

## 5. Reference Material in This Package

- `reference/prototype.py` — Working slide generator from initial exploration. Use as architectural reference; **don't copy verbatim**. Refactor into the modular structure above with proper separation, type hints, and tests.
- `reference/sample_output.pdf` — What the prototype produced for "Because He Lives". Visual target.
- `assets/background.png` — The user's actual Canva background, to be used as `backend/assets/background.png`.

## 6. Working Style — Important

The user (Bhanu) wants to **drive** this project, not just receive code. He's adding it to his portfolio for job applications, so deep understanding matters.

- **Explain before you code.** When starting a milestone, briefly state the plan and ask if he agrees before writing files.
- **Commit in meaningful chunks.** Each milestone = at least one logical commit with a clear message. The Git history itself is part of the deliverable.
- **Teach, don't just deliver.** When you make a non-obvious technical decision (e.g., "I used `BackgroundTasks` here because..."), say why in 1–2 lines. He should be able to walk through the codebase in an interview.
- **Push back when warranted.** If he asks for something that conflicts with v1 scope or introduces unnecessary complexity, say so. He explicitly asked for honest guidance.
- **Don't over-format responses.** Plain explanations, code blocks where needed. No walls of bullet points.

## 7. Known Risks & v1.1 Ideas

Document these in the README's "Roadmap" section once shipped, so the project tells a coherent forward story:

- **Background flexibility:** Let users upload their own background or pick from presets.
- **Font flexibility:** Multiple bundled fonts (Poppins, Montserrat, Bebas Neue, etc.).
- **Multi-line auto-pairing:** Currently splits into N-line chunks; could detect rhyme/punctuation pairs and split smarter.
- **Lyrics scraper:** Pull lyrics from Genius API given a song name, with section markers already in place.
- **YouTube flow detection:** The big one. Whisper transcription + lyric alignment to auto-suggest performance order. Human-in-the-loop review.
- **Export formats:** PPTX export in addition to PDF, for editing in PowerPoint/Keynote.
- **Deployment:** Backend on Fly.io / Railway, frontend on Vercel. Simple Docker setup for the backend.
