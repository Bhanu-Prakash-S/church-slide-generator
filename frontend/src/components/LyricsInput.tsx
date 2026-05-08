interface Props {
  value: string
  onChange: (val: string) => void
}

const MARKERS = ['[Verse 1]', '[Verse 2]', '[Chorus]', '[Bridge]', '[Pre-Chorus]']

export default function LyricsInput({ value, onChange }: Props) {
  function insertMarker(marker: string) {
    const newline = value.length > 0 && !value.endsWith('\n') ? '\n\n' : ''
    onChange(value + newline + marker + '\n')
  }

  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-semibold text-gray-700">
        Lyrics
        <span className="ml-2 text-xs font-normal text-gray-400">
          (use [Section] headers to mark each section)
        </span>
      </label>

      <div className="flex flex-wrap gap-1">
        {MARKERS.map((m) => (
          <button
            key={m}
            onClick={() => insertMarker(m)}
            className="px-2 py-0.5 text-xs rounded border border-gray-300 bg-white hover:bg-gray-50 text-gray-600 cursor-pointer"
          >
            {m}
          </button>
        ))}
      </div>

      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={18}
        placeholder={"[Verse 1]\nGod sent His Son,\nThey called Him, Jesus\n...\n\n[Chorus]\nBecause He lives,\n..."}
        spellCheck={false}
        className="w-full rounded-lg border border-gray-300 p-3 text-sm font-mono leading-relaxed resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400"
      />
    </div>
  )
}
