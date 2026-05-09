# Roadmap

Milestone-driven plan. Each milestone is a working, committable state.
Don't move to the next until the current one passes review.

---

## STATUS SNAPSHOT

- **v1.0 — Complete and deployed.** Milestones 0–5 shipped.
  Live at: https://song-slides-generator.vercel.app (frontend) + Railway (backend)
- **Now building: v1.1 — Smart Input.** Start at Milestone 6.

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

## 🔨 IN PROGRESS — v1.1: Smart Input

The problem v1.1 solves: users have to manually add `[Verse 1]`, `[Chorus]`, etc. to lyrics before the tool works. This is friction. v1.1 eliminates it with a database of known songs + AI fallback.

### Architecture decisions made

**Second Brain (English song database)**
- The project has a `assets/Songs Book.pdf` — a 438-page hymnal.
- English songs start at ~page 246, run to ~page 430. ~150 songs total.
- English text extracts cleanly from the PDF (text-based, not scanned).
- Telugu songs (~pages 1–245) use a legacy custom font encoding — text comes out garbled. Deferred to v1.2.
- One-time extraction script builds a JSON database: `{ title, number, lyrics, sections, source: "book" }`.
- `source` flag: `"book"` = extracted from PDF, `"manual"` = overridden by user. Manual entries are never overwritten on re-extraction.

**Detect Sections approach**
- When user clicks "Detect Sections": fuzzy-match pasted lyrics against the database first.
- If match found (confidence > 85%): apply known section structure instantly. Free, instant, 100% accurate.
- If no match (Telugu, or song not in book): fall back to Claude Haiku 4.5 for AI-based structure detection.
- Claude Haiku analyzes the lyrics text structurally — it does NOT search the internet. It reads line grouping, repetition patterns, and rhyme scheme to infer sections.
- Cost estimate for AI fallback: ~$0.003 per song. 100 songs ≈ $0.30.

**Performance order presets**
- Two preset chips: "Chorus Theme" → `V1, C, V2, C, V3, C` and "Hymn" → `V1, V2, V3`.
- Manual input still works unchanged.

---

### Milestone 6: Performance Order Presets
**Goal:** Two preset chips above the performance order input. One click fills the order string.

**Changes:**
- `frontend/src/components/OrderInput.tsx` — add two preset buttons above the text input.
  - "Chorus Theme" fills `V1, C, V2, C, V3, C`
  - "Hymn" fills `V1, V2, V3`
- No backend changes.

**Done when:** Clicking each preset fills the order field correctly. Manual typing still works.

**Commit:** `feat(frontend): performance order preset chips`

---

### Milestone 7: English Song Database
**Goal:** A clean, searchable JSON database of all English songs extracted from the PDF.

**Changes:**
- New script: `backend/scripts/extract_songs.py`
  - Reads `assets/Songs Book.pdf` pages 246–438 using `pdfplumber`
  - Parses song number, title, verses, and chorus
  - Outputs `backend/assets/songs_db.json`
- Schema per entry:
  ```json
  {
    "id": 16,
    "title": "Amazing Grace",
    "title_normalized": "amazing grace",
    "lyrics": "[Verse 1]\nAmazing grace...\n\n[Chorus]\n...",
    "sections": { "V1": ["Amazing grace!", "How sweet the sound"], "C": ["..."] },
    "source": "book",
    "page": 246
  }
  ```
- `songs_db.json` is committed to the repo (it's a static asset, not a build artifact).

**Done when:** Script runs cleanly, all ~150 English songs extracted with correct titles and section structure. Spot-check 10 songs manually.

**Commit:** `feat(backend): one-time English song extraction script + songs_db.json`

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
