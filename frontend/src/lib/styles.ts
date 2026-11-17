export type ButtonVariant = 'primary' | 'secondary' | 'danger'

const base =
  'inline-flex items-center justify-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:cursor-not-allowed disabled:opacity-60'

const variants: Record<ButtonVariant, string> = {
  primary: 'bg-indigo-600 text-white hover:bg-indigo-700',
  secondary: 'border border-slate-300 bg-white text-slate-800 hover:bg-slate-50',
  danger: 'border border-red-200 bg-white text-red-700 hover:bg-red-50',
}

/** Shared by <Button> and button-styled <Link>s. */
export function buttonClass(variant: ButtonVariant = 'primary', extra = '') {
  return `${base} ${variants[variant]} ${extra}`.trim()
}

export const linkClass =
  'rounded-sm font-medium text-indigo-700 underline-offset-2 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600'

export const inputClass =
  'block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-slate-900 shadow-sm focus-visible:border-indigo-600 focus-visible:outline-2 focus-visible:outline-indigo-600 aria-invalid:border-red-500'
