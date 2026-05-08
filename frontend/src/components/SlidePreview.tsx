import type { ValidateResponse } from '../api/client'

interface Props {
  validation: ValidateResponse | null
  loading: boolean
  error: string | null
}

export default function SlidePreview({ validation, loading, error }: Props) {
  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold text-gray-700">Preview</h2>

      {loading && (
        <p className="text-sm text-gray-400 animate-pulse">Validating…</p>
      )}

      {error && !loading && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {validation && !loading && !error && (
        <div className="flex flex-col gap-3">
          {validation.missing_sections.length > 0 && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
              Missing sections:{' '}
              <span className="font-mono font-semibold">
                {validation.missing_sections.join(', ')}
              </span>
              <br />
              <span className="text-xs">
                Add these sections to your lyrics or remove them from the order.
              </span>
            </div>
          )}

          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <span
                className={`inline-block w-2 h-2 rounded-full ${
                  validation.valid ? 'bg-green-500' : 'bg-amber-400'
                }`}
              />
              <span className="text-sm font-medium text-gray-700">
                {validation.valid ? 'Ready to generate' : 'Has missing sections'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm mt-1">
              <span className="text-gray-500">Sections found</span>
              <span className="font-mono text-gray-800">
                {validation.sections_found.join(', ')}
              </span>

              <span className="text-gray-500">Order</span>
              <span className="font-mono text-gray-800">
                {validation.order_parsed.join(', ')}
              </span>

              <span className="text-gray-500">Slide count</span>
              <span className="font-semibold text-indigo-700 text-base">
                {validation.estimated_slide_count}
              </span>
            </div>
          </div>
        </div>
      )}

      {!validation && !loading && !error && (
        <div className="rounded-lg border border-dashed border-gray-200 p-8 text-center text-sm text-gray-400">
          Paste your lyrics and order to see a preview
        </div>
      )}
    </div>
  )
}
