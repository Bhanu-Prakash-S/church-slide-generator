import { useState, useEffect, useRef } from 'react'
import { validateSlides, type ValidateResponse } from './api/client'
import LyricsInput from './components/LyricsInput'
import OrderInput from './components/OrderInput'
import SlidePreview from './components/SlidePreview'
import GenerateButton from './components/GenerateButton'

const SAMPLE_LYRICS = `[Verse 1]
God sent His Son,
They called Him, Jesus
He came to love,
Heal and forgive;
He lived and died
To buy my pardon,
An empty grave is there
To prove my Savior lives!

[Chorus]
Because He lives,
I can face tomorrow!
Because He lives,
All fear is gone
Because I know
He holds the future,
And life is worth the living,
Just because He lives!

[Verse 2]
How sweet to hold
A newborn baby,
And feel the pride
And joy he brings
But greater still
The calm assurance
This child can face
Uncertain days because He Lives!

[Verse 3]
And then one day,
I'll cross the river,
I'll fight life's final
War with pain
And then, as death
Gives way to victory,
I'll see the lights of glory
And I'll know He lives!`

const SAMPLE_ORDER = 'V1, C, V2, C, V3, C'

export default function App() {
  const [lyrics, setLyrics] = useState('')
  const [order, setOrder] = useState('')
  const [filename, setFilename] = useState('')
  const [validation, setValidation] = useState<ValidateResponse | null>(null)
  const [validating, setValidating] = useState(false)
  const [validationError, setValidationError] = useState<string | null>(null)

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!lyrics.trim() || !order.trim()) {
      setValidation(null)
      setValidationError(null)
      return
    }

    if (debounceRef.current) clearTimeout(debounceRef.current)

    debounceRef.current = setTimeout(async () => {
      setValidating(true)
      setValidationError(null)
      try {
        const result = await validateSlides(lyrics, order)
        setValidation(result)
      } catch {
        setValidationError('Could not reach the backend. Is it running?')
        setValidation(null)
      } finally {
        setValidating(false)
      }
    }, 500)

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [lyrics, order])

  function loadSample() {
    setLyrics(SAMPLE_LYRICS)
    setOrder(SAMPLE_ORDER)
    setFilename('because_he_lives')
  }

  const canGenerate = !!validation?.valid

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-gray-900">Church Slide Generator</h1>
            <p className="text-sm text-gray-500">Paste lyrics → get a PDF in seconds</p>
          </div>
          <button
            onClick={loadSample}
            className="text-sm text-indigo-600 hover:text-indigo-800 underline cursor-pointer"
          >
            Try a sample
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left panel — inputs */}
          <div className="flex flex-col gap-6">
            <LyricsInput value={lyrics} onChange={setLyrics} />
            <OrderInput value={order} onChange={setOrder} />
            <div className="flex flex-col gap-2">
              <label className="text-sm font-semibold text-gray-700">
                Filename
                <span className="ml-2 text-xs font-normal text-gray-400">optional</span>
              </label>
              <input
                type="text"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
                placeholder="because_he_lives"
                className="w-full rounded-lg border border-gray-300 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
            </div>
          </div>

          {/* Right panel — preview + generate */}
          <div className="flex flex-col gap-6">
            <SlidePreview
              validation={validation}
              loading={validating}
              error={validationError}
            />
            <GenerateButton
              lyrics={lyrics}
              order={order}
              filename={filename}
              disabled={!canGenerate}
            />
          </div>
        </div>
      </main>
    </div>
  )
}
