import type { ReactNode } from 'react'

type Aria = { id: string; 'aria-describedby'?: string; 'aria-invalid'?: true }

type Props = {
  id: string
  label: string
  hint?: ReactNode
  error?: string
  /** Render the control; spread the given props onto it so label, hint and error are linked. */
  children: (aria: Aria) => ReactNode
}

export function Field({ id, label, hint, error, children }: Props) {
  const hintId = hint ? `${id}-hint` : undefined
  const errorId = error ? `${id}-error` : undefined
  const describedBy = [hintId, errorId].filter(Boolean).join(' ') || undefined
  return (
    <div className="space-y-1">
      <label htmlFor={id} className="block text-sm font-medium text-slate-800">
        {label}
      </label>
      {children({ id, 'aria-describedby': describedBy, 'aria-invalid': error ? true : undefined })}
      {hint && (
        <div id={hintId} className="text-xs text-slate-500">
          {hint}
        </div>
      )}
      {error && (
        <p id={errorId} className="text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  )
}
