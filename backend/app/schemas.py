from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    lyrics: str = Field(..., min_length=1)
    order: str = Field(..., min_length=1)
    filename: str = Field(default="slides")


class ValidateResponse(BaseModel):
    valid: bool
    sections_found: list[str]
    order_parsed: list[str]
    missing_sections: list[str]
    estimated_slide_count: int
