import tempfile
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.parsing import parse_sections, parse_order
from app.schemas import GenerateRequest, ValidateResponse
from app.slides import chunk_section, expand_long_lines, generate_pdf

app = FastAPI(title="Church Slide Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/validate", response_model=ValidateResponse)
def validate(req: GenerateRequest):
    sections = parse_sections(req.lyrics)
    order = parse_order(req.order)

    missing = [key for key in order if key not in sections]
    slide_count = sum(
        len(chunk_section(expand_long_lines(sections[key])))
        for key in order
        if key in sections
    )

    return ValidateResponse(
        valid=len(missing) == 0,
        sections_found=list(sections.keys()),
        order_parsed=order,
        missing_sections=missing,
        estimated_slide_count=slide_count,
    )


@app.post("/api/generate-slides")
def generate_slides(req: GenerateRequest):
    sections = parse_sections(req.lyrics)
    order = parse_order(req.order)

    missing = [key for key in order if key not in sections]
    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Sections in order not found in lyrics: {', '.join(missing)}",
        )

    if not sections:
        raise HTTPException(status_code=400, detail="No sections found in lyrics.")

    # Write to a temp file — FileResponse streams it and cleans up via background task
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    out_path = Path(tmp.name)

    try:
        generate_pdf(sections, order, out_path)
    except Exception as e:
        out_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(e))

    filename = f"{req.filename}.pdf" if req.filename else "slides.pdf"
    return FileResponse(
        path=out_path,
        media_type="application/pdf",
        filename=filename,
        background=_cleanup(out_path),
    )


class _cleanup:
    """Delete the temp PDF after the response is sent."""
    def __init__(self, path: Path):
        self.path = path

    async def __call__(self):
        self.path.unlink(missing_ok=True)
