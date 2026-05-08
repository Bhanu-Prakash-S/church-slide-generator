// In dev, VITE_API_URL is unset so API_BASE is '' and Vite's proxy rewrites /api → localhost:8000.
// In production, VITE_API_URL is set to the Railway backend URL (e.g. https://your-app.railway.app).
const API_BASE = import.meta.env.VITE_API_URL ?? ''

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
  const res = await fetch(`${API_BASE}/api/validate`, {
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
  const res = await fetch(`${API_BASE}/api/generate-slides`, {
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
