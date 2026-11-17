import type { ApiError } from '../api/client'

export type FieldErrors = Record<string, string>

const FALLBACK = 'Something went wrong. Please try again.'

function isApiError(error: unknown): error is ApiError {
  return typeof error === 'object' && error !== null && typeof (error as ApiError).message === 'string'
}

/** Turn an openapi-fetch `error` body (or a thrown Error) into a message for the user. */
export function errorMessage(error: unknown, fallback = FALLBACK): string {
  if (isApiError(error) && error.message) return error.message
  if (error instanceof Error && error.message) return error.message
  return fallback
}

/** Map 422 `details` [{loc, msg}] to { fieldName: msg }; the last `loc` element is the camelCase field. */
export function fieldErrors(error: unknown): FieldErrors {
  const details = isApiError(error) ? error.details : undefined
  const out: FieldErrors = {}
  if (!Array.isArray(details)) return out
  for (const d of details) {
    const loc = (d as { loc?: unknown }).loc
    const msg = (d as { msg?: unknown }).msg
    if (!Array.isArray(loc) || typeof msg !== 'string' || loc.length === 0) continue
    const field = String(loc[loc.length - 1])
    out[field] ??= msg
  }
  return out
}
