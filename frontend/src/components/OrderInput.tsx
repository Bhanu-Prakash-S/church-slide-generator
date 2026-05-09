const PRESETS = [
  { label: "Chorus Theme", value: "V1, C, V2, C, V3, C" },
  { label: "Hymn",         value: "V1, V2, V3" },
]

interface Props {
  value: string
  onChange: (val: string) => void
}

export default function OrderInput({ value, onChange }: Props) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-semibold text-gray-700">
        Performance order
        <span className="ml-2 text-xs font-normal text-gray-400">
          comma-separated section keys
        </span>
      </label>
      <div className="flex gap-2">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            type="button"
            onClick={() => onChange(p.value)}
            className="rounded-full border border-indigo-300 bg-indigo-50 px-3 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100 transition-colors"
          >
            {p.label}
          </button>
        ))}
      </div>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="V1, C, V2, C, V3, C"
        className="w-full rounded-lg border border-gray-300 p-3 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-indigo-400"
      />
      <p className="text-xs text-gray-400">
        Keys: V1 V2 V3 = Verse, C C2 = Chorus, B = Bridge, PC = Pre-Chorus, I = Intro, O = Outro
      </p>
    </div>
  )
}
