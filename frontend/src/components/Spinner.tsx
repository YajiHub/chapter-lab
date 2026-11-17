export function Spinner({ label = 'Loading…', center = false }: { label?: string; center?: boolean }) {
  return (
    <div
      role="status"
      className={`flex items-center gap-3 text-slate-600 ${center ? 'min-h-[50vh] justify-center' : 'py-6'}`}
    >
      <span
        aria-hidden="true"
        className="size-5 animate-spin rounded-full border-2 border-slate-300 border-t-indigo-600"
      />
      <span>{label}</span>
    </div>
  )
}
