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
