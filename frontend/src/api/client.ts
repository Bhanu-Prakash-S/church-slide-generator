export interface ValidateResponse {
  valid: boolean
  sections_found: string[]
  order_parsed: string[]
  missing_sections: string[]
  estimated_slide_count: number
}

export async function validateSlides(
  lyrics: string,
  order: string
): Promise<ValidateResponse> {
  const res = await fetch('/api/validate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lyrics, order }),
  })
  if (!res.ok) throw new Error('Validation request failed')
  return res.json()
}

export async function generateSlides(
  lyrics: string,
  order: string,
  filename: string
): Promise<Blob> {
  const res = await fetch('/api/generate-slides', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lyrics, order, filename }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Server error ${res.status}`)
  }
  return res.blob()
}
