# Church Slide Generator

> Paste lyrics → get a styled PDF in seconds.

A web app that turns section-marked lyrics and a performance order string into church song slides as a PDF — replacing a 15–30 minute weekly Canva + iLovePDF workflow.

**[Live demo →](https://church-slide-generator.vercel.app)**

---

## Why I built this

Every week I prepare song slides for my church. The workflow: watch a YouTube video to learn the song's performance order, open Canva, manually lay out each slide, adjust font sizes so nothing overflows, export a 50–90 MB PDF, then compress it on iLovePDF.com before it can be used.

This project automates all of that. Paste the lyrics with section markers, type the order, click Generate. The PDF comes out at 1–3 MB natively — no external compression step needed.

---

## Features

- **Section-marked lyrics** — paste with `[Verse 1]`, `[Chorus]`, `[Bridge]` headers
- **Performance order** — write `V1, C, V2, C, V3, C` once; the app repeats sections automatically
- **Smart line splitting** — long lines are split at natural phrase boundaries (commas, semicolons, conjunctions) so the font stays large and readable
- **Live preview** — see the slide count and catch missing sections before generating
- **Small PDFs** — 1–3 MB output; `img2pdf` wraps images directly into PDF without recompressing

---

## Quick start

### Prerequisites

- Python 3.14+ with [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 18+

### 1. Clone

```bash
git clone https://github.com/Bhanu-Prakash-S/church-slide-generator.git
cd church-slide-generator
```

### 2. Backend

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
# Running at http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Running at http://localhost:5173
```

Open **http://localhost:5173**, click **"Try a sample"** to load example lyrics, then hit **Generate PDF**.

### Docker (backend only)

```bash
cd backend
docker build -t church-slide-generator .
docker run -p 8000:8000 church-slide-generator
```

---

## How it works

```
Browser (React + Vite)              Backend (FastAPI + Python)
┌──────────────────────┐            ┌─────────────────────────────────┐
│  Paste lyrics        │            │  POST /api/validate             │
│  Set order           │ ─────────▶ │    parse_sections()             │
│  Live preview        │ ◀───────── │    parse_order()                │
│                      │            │    expand_long_lines()          │
│  Generate PDF ──────────────────▶ │  POST /api/generate-slides      │
│  ← downloads file    │ ◀───────── │    render_slide()  [Pillow]     │
└──────────────────────┘            │    img2pdf.convert()            │
                                    └─────────────────────────────────┘
```

**Key decisions:**

**Pillow + img2pdf instead of headless Chrome or ReportLab** — the slide design is a fixed background image with large stroked text. Raster rendering with Pillow is the most direct fit; `img2pdf` then wraps the JPEG bytes directly into the PDF container without a second compression pass, which is why output files are 1–3 MB instead of 50+ MB.

**FastAPI** — one meaningful endpoint, minimal framework overhead, streams the PDF response directly so the file downloads without a round-trip through JavaScript blob storage.

**Smart line splitting** — lines that exceed 6 effective words and won't fit at the standard font size are split near a natural phrase boundary (comma, semicolon, then conjunctions like "and"/"but"). This keeps the font consistently large across all songs rather than shrinking to accommodate wide lines.

---

## Input format

**Lyrics** (with section markers):
```
[Verse 1]
God sent His Son,
They called Him, Jesus
He came to love,
Heal and forgive;

[Chorus]
Because He lives,
I can face tomorrow!
```

**Performance order:**
```
V1, C, V2, C, V3, C
```

| Key | Section |
|-----|---------|
| V1, V2, V3 | Verse 1, 2, 3 |
| C, C2 | Chorus, Chorus 2 |
| B | Bridge |
| PC | Pre-Chorus |
| I | Intro |
| O | Outro |

---

## Tech stack

| | Technology | Why |
|---|---|---|
| Backend | Python 3.14, FastAPI | Pillow is Python-native; FastAPI is minimal overhead for a single endpoint |
| Rendering | Pillow | Raster rendering handles background image + stroked text naturally |
| PDF assembly | img2pdf | Lossless JPEG-to-PDF conversion keeps file sizes small |
| Frontend | React 19, TypeScript, Vite | SPA with no SSR needed; Vite proxy removes CORS complexity in dev |
| Styling | Tailwind CSS v4 | Utility-first keeps the component code concise |
| Font | Poppins Bold | Clean, bold, legible at large sizes on dark backgrounds |
| Package manager | uv | Fast, reproducible Python environments with lockfile |

---

## Project structure

```
church-slide-generator/
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI app — endpoints and PDF streaming
│   │   ├── slides.py      # Core engine — rendering, chunking, line splitting
│   │   ├── parsing.py     # Lyrics and order parsing
│   │   ├── config.py      # Style constants (canvas size, font, colors)
│   │   └── schemas.py     # Pydantic request/response models
│   ├── assets/            # background.png and Poppins-Bold.ttf
│   ├── tests/             # 34 pytest tests
│   └── Dockerfile
└── frontend/
    └── src/
        ├── App.tsx                    # State, debounced validation
        ├── api/client.ts              # Typed fetch wrappers
        └── components/
            ├── LyricsInput.tsx        # Textarea with section-marker helpers
            ├── OrderInput.tsx         # Order input with key reference
            ├── SlidePreview.tsx       # Live validation feedback
            └── GenerateButton.tsx     # PDF download trigger
```

---

## Roadmap

Milestones completed: repo setup → slide engine → API → frontend → polish. See [ROADMAP.md](ROADMAP.md) for the full history.

**v1.1 ideas:**
- Custom background upload or preset gallery
- PPTX export for editing in PowerPoint / Keynote
- Lyrics scraper — paste a song title, pull structured lyrics from Genius API
- YouTube flow detection — Whisper transcription + lyric alignment to auto-suggest performance order (human-in-the-loop review)

---

## License

[MIT](LICENSE)
