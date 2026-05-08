from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FIXTURE = Path(__file__).parent / "fixtures" / "because_he_lives.txt"
LYRICS = FIXTURE.read_text(encoding="utf-8")
ORDER = "V1, C, V2, C, V3, C"


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_validate_valid():
    r = client.post("/api/validate", json={"lyrics": LYRICS, "order": ORDER})
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert set(body["sections_found"]) == {"V1", "C", "V2", "V3"}
    assert body["order_parsed"] == ["V1", "C", "V2", "C", "V3", "C"]
    assert body["missing_sections"] == []
    assert body["estimated_slide_count"] == 12


def test_validate_missing_section():
    r = client.post("/api/validate", json={"lyrics": LYRICS, "order": "V1, C, B"})
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert "B" in body["missing_sections"]


def test_generate_slides_returns_pdf():
    r = client.post(
        "/api/generate-slides",
        json={"lyrics": LYRICS, "order": ORDER, "filename": "test_output"},
    )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 100_000  # should be a real PDF, not empty


def test_generate_slides_missing_section_returns_400():
    r = client.post(
        "/api/generate-slides",
        json={"lyrics": LYRICS, "order": "V1, C, B"},
    )
    assert r.status_code == 400
    assert "B" in r.json()["detail"]


def test_generate_slides_empty_lyrics_returns_422():
    r = client.post("/api/generate-slides", json={"lyrics": "", "order": ORDER})
    assert r.status_code == 422
