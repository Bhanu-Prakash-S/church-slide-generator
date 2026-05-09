# Roadmap

Milestone-driven plan. Each milestone is a working, committable state.
Don't move to the next until the current one passes review.

---

## STATUS SNAPSHOT

- **v1.0 — Complete and deployed.** Milestones 0–5 shipped.
  Live at: https://song-slides-generator.vercel.app (frontend) + Railway (backend)
- **v1.1 — In progress.** Milestones 6 and 7 shipped. **Resume at Milestone 8.**

---

## ✅ COMPLETED — v1.0

### Milestone 0: Repo Setup ✅
Git repo, README, LICENSE, .gitignore, backend/ and frontend/ scaffolded.

### Milestone 1: Backend Slide Engine ✅
`parsing.py`, `slides.py`, `config.py`, `schemas.py` implemented and tested.
Pillow renders 1920×1080 slides with custom background, Poppins Bold, white text + black stroke.
`img2pdf` assembles slides into a 1–3 MB PDF natively (no external compression needed).

### Milestone 2: FastAPI Wrapper ✅
`POST /api/generate-slides` — returns a streamed PDF.
`POST /api/validate` — returns parsed section structure + slide count for live preview.
`GET /health` — health check.

### Milestone 3: React Frontend ✅
Two-panel layout: lyrics + order input on the left, slide preview + generate on the right.
Live debounced validation (500ms). Inline error display. PDF download on click.

### Milestone 4: Polish & Edge Cases ✅
Loading states, "Try a sample" button, special character handling, Dockerfile.

### Milestone 5: README & Deploy ✅
Deployed to Railway (backend) + Vercel (frontend). README with architecture, tech stack, and "why I built this." v1.0.0 tagged.

---

## ✅ COMPLETED — v1.1 (partial)

### Architecture decisions made

**Second Brain (English song database)**
- The project has `assets/Songs Book.pdf` — a 438-page hymnal.
- English songs span pages 234–417 (0-indexed: 233–417). Two collections: traditional hymns (pp 234–355) and contemporary worship (pp 356–417). 298 songs total.
- English text extracts cleanly via pdfplumber. Telugu songs (~pp 1–233) use legacy custom font encoding — garbled, deferred.
- One-time extraction script builds a JSON database per entry: `{ number, title, title_normalized, sections, source, page }`.
- `source` flag: `"book"` = extracted from PDF, `"manual"` = overridden by user. Manual entries are never overwritten on re-extraction.
- Paragraph detection uses y-coordinate gaps (not blank lines). Dual threshold: traditional ≥ 16px, contemporary ≥ 21px.
- `smart_split()` resolves page-boundary verse merges without breaking genuine 8-line stanzas.

**Detect Sections approach**
- When user clicks "Detect Sections": fuzzy-match pasted lyrics against the database first.
- If match found (confidence > 85%): apply known section structure instantly. Free, instant, 100% accurate.
- If no match (Telugu, or song not in book): fall back to Claude Haiku 4.5 for AI-based structure detection.
- Claude Haiku analyzes lyrics structurally (line grouping, repetition, rhyme scheme) — no internet access.
- Cost estimate for AI fallback: ~$0.003 per song. 100 songs ≈ $0.30.

**Performance order presets**
- Two preset chips: "Chorus Theme" → `V1, C, V2, C, V3, C` and "Hymn" → `V1, V2, V3`.
- Manual input still works unchanged.

---

### Milestone 6: Performance Order Presets ✅
**Goal:** Two preset chips above the performance order input. One click fills the order string.

**Changes made:**
- `frontend/src/components/OrderInput.tsx` — added two rounded chip buttons above the text input.
  - "Chorus Theme" fills `V1, C, V2, C, V3, C`
  - "Hymn" fills `V1, V2, V3`

**Commit:** `feat(frontend): performance order preset chips` (c59beb9)

---

### Milestone 7: English Song Database ✅
**Goal:** A clean, searchable JSON database of all English songs extracted from the PDF.

**Changes made:**
- `backend/scripts/extract_songs.py` — one-time extraction script. Run from repo root: `python backend/scripts/extract_songs.py`. Requires `pdfplumber` (`pip install pdfplumber`).
- `backend/assets/songs_db.json` — 298 English songs. Committed as a static asset.
- Actual schema per entry (no `lyrics` field — sections only):
  ```json
  {
    "number": 16,
    "title": "Amazing Grace",
    "title_normalized": "amazing grace",
    "sections": { "V1": ["Amazing grace!", "How sweet the sound"], "C": ["..."] },
    "source": "book",
    "page": 246
  }
  ```

**Commit:** `feat(backend): one-time English song extraction script + songs_db.json` (6cf7ff6)

---

## 🔨 IN PROGRESS — v1.1: Smart Input

The problem v1.1 solves: users have to manually add `[Verse 1]`, `[Chorus]`, etc. to lyrics before the tool works. This is friction. v1.1 eliminates it with a database of known songs + AI fallback.

**Resume here: Milestone 8.**

---

### Milestone 8: Detect Sections Button
**Goal:** "Detect Sections" button on the lyrics input that auto-adds section markers.

**Changes:**
- New backend endpoint: `POST /api/detect-sections`
  - Input: `{ "lyrics": "raw lyrics text" }`
  - Step 1: fuzzy-match against `songs_db.json` (match on first 3–4 lines)
  - Step 2: if no match, call Claude Haiku 4.5 to detect structure
  - Output: `{ "lyrics": "lyrics with [Section] markers added", "source": "database" | "ai" }`
- `frontend/src/components/LyricsInput.tsx` — add "Detect Sections" button next to label
  - Disabled if markers already present in the textarea
  - Shows a loading spinner while detecting
  - On success: replaces textarea content with marked-up lyrics
  - Shows a subtle badge: "Found in database" or "Detected by AI"

**Done when:** Pasting raw English lyrics and clicking the button correctly adds section markers. AI fallback works for a song not in the database.

**Commit:** `feat: detect sections via database lookup with AI fallback`

---

### Milestone 9: Song Name Search
**Goal:** User types a song name, selects from results, lyrics auto-populate.

**Changes:**
- New backend endpoint: `POST /api/search-songs`
  - Input: `{ "query": "amazing grace" }`
  - Fuzzy search against `songs_db.json` titles
  - Returns top 5 matches: `[{ "id", "title", "number" }]`
- New backend endpoint: `GET /api/songs/{id}`
  - Returns full song entry (lyrics + sections)
- `frontend/src/App.tsx` — add a search field above the lyrics textarea
  - Debounced search as user types (300ms)
  - Dropdown of results below the field
  - Clicking a result populates the lyrics textarea + clears the order field
  - Field disappears / collapses once a song is selected (keeps UI minimal)

**Done when:** Typing "amazing" shows "Amazing Grace" in results. Clicking it populates the lyrics. User can still manually paste lyrics if they prefer.

**Commit:** `feat: song name search with auto-populate from database`

---

## 📋 PLANNED — v1.2

### Milestone 10: Song Override / Update
**Goal:** Individual song entries in the database can be corrected without re-running extraction.

- A simple backend script (or API endpoint): accepts song name + corrected lyrics → finds the entry → updates it → sets `source: "manual"`.
- Manual entries are never overwritten if extraction is re-run.
- This handles cases where the book has outdated lyrics and the user has the corrected version.

---

## 🔮 DEFERRED

### Telugu Song Support
The PDF's Telugu section (~pages 1–245) uses a legacy custom font encoding (not Unicode). Extracted text is garbled and cannot be matched against user-pasted lyrics. Options when we revisit:
1. Decode the font mapping (requires identifying which encoding — Nudi, TSCII, etc.)
2. OCR with Telugu language support (Tesseract + Telugu model)
3. User supplies a Unicode version of the Telugu section

Until then: Telugu songs fall through to the Claude Haiku AI fallback in Milestone 8, which can detect structure from Telugu text since repetition patterns are language-agnostic.

### Other deferred ideas (from original PROJECT_BRIEF.md)
- Background / font customization
- Lyrics scraper (Genius API)
- YouTube flow detection (Whisper transcription + lyric alignment)
- PPTX export
- User accounts / saved songs
