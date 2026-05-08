# Roadmap

Milestone-driven plan. Each milestone is a working, committable state. Don't move to the next until the current one is green.

---

## Milestone 0: Repo Setup
**Goal:** Empty but properly initialized repo on GitHub.

- [ ] `git init` and create initial commit with README, .gitignore, PROJECT_BRIEF.md, ROADMAP.md
- [ ] Create public GitHub repo, push
- [ ] Set up `backend/` and `frontend/` directories with placeholder files
- [ ] Add MIT license

**Done when:** Repo is browsable on GitHub with clear README explaining project purpose.

---

## Milestone 1: Backend Slide Engine
**Goal:** A `slides.py` module that, given parsed lyrics + order, produces a PDF on disk.

- [ ] Set up Python env (recommend `uv` for speed, or poetry)
- [ ] Install Pillow, img2pdf, pytest
- [ ] Implement `parsing.py`:
  - `parse_sections(lyrics_text) -> dict[str, list[str]]`
  - `parse_order(order_str) -> list[str]`
  - `normalize_section_key(name) -> str`
- [ ] Implement `slides.py`:
  - `chunk_section(lines, lines_per_slide=4) -> list[list[str]]`
  - `render_slide(lines, bg_image, config) -> PIL.Image`
  - `generate_pdf(lyrics, order, output_path) -> Path`
- [ ] `config.py` with all style constants (canvas size, colors, font path, etc.)
- [ ] Tests with the "Because He Lives" fixture — assert slide count, section order, parsing correctness
- [ ] CLI entry point: `python -m app.slides --input lyrics.txt --order "V1,C,V2,C" --out out.pdf`

**Done when:** `pytest` passes and the CLI produces a PDF visually equivalent to `reference/sample_output.pdf`.

**Commit:** `feat(backend): slide engine with parsing, chunking, and PDF generation`

---

## Milestone 2: FastAPI Wrapper
**Goal:** HTTP endpoint serving the engine.

- [ ] Add FastAPI + uvicorn
- [ ] Implement `main.py` with:
  - `POST /api/generate-slides` (returns PDF stream)
  - `POST /api/validate` (returns parsed structure for preview)
  - `GET /health`
- [ ] Pydantic schemas in `schemas.py`
- [ ] CORS middleware for local frontend dev
- [ ] Error handling: invalid lyrics format, missing sections in order, etc. Return clear 400 responses.
- [ ] Add API tests with FastAPI TestClient

**Done when:** `curl` against the running server returns a valid PDF.

**Commit:** `feat(backend): FastAPI endpoints for slide generation and validation`

---

## Milestone 3: React Frontend
**Goal:** Working UI to generate and download a PDF.

- [ ] Scaffold with Vite + React + TypeScript
- [ ] Components:
  - `LyricsInput` (textarea with section-marker helper buttons)
  - `OrderInput` (text input with example placeholder)
  - `SlidePreview` (renders first slide as image, shows total slide count — call `/api/validate`)
  - `GenerateButton` (calls `/api/generate-slides`, triggers download)
- [ ] API client in `api/client.ts`
- [ ] Debounced validation on input change (500ms)
- [ ] Inline error display for validation failures
- [ ] Basic styling — clean, readable, no design overengineering. Tailwind is fine.

**Done when:** End-to-end flow works: paste lyrics → see preview → click button → PDF downloads.

**Commit:** `feat(frontend): React UI with live preview and PDF download`

---

## Milestone 4: Polish & Edge Cases
**Goal:** Project is presentable in a portfolio review.

- [ ] Loading states on the generate button
- [ ] Helpful empty states ("paste your lyrics to get started")
- [ ] Handle long sections gracefully (sections with 20+ lines)
- [ ] Handle special characters (apostrophes, em-dashes, accents) in font rendering
- [ ] Add a "Try a sample" button that loads "Because He Lives" lyrics + order
- [ ] Frontend builds without warnings
- [ ] Backend has a Dockerfile

**Commit:** `polish: loading states, samples, edge case handling`

---

## Milestone 5: README & Deploy
**Goal:** A stranger can find the repo, understand it, and use it.

- [ ] README with:
  - Screenshot/GIF of the tool in action
  - Quick start (clone → install → run)
  - Architecture overview (1 paragraph + a simple diagram)
  - Tech stack and reasoning
  - Roadmap section (link to ROADMAP.md, mention v1.1 ideas)
  - "Why I built this" section — personal context, the Canva → iLovePDF workflow
- [ ] Deploy backend to Fly.io or Railway
- [ ] Deploy frontend to Vercel
- [ ] Live URL in README
- [ ] Tag a `v1.0.0` release

**Commit:** `docs: complete README with screenshots, architecture, and deployment links`

**This is the milestone that makes the project portfolio-ready.** Don't skip.

---

## Time Estimate

If working focused 4–6 hours per day: 2–4 days end-to-end. Don't try to ship it all in one sitting — the commit history matters.
