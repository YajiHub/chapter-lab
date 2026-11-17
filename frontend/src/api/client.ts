import createClient, { type Middleware } from 'openapi-fetch'
import type { paths } from './schema'

// Set from login / me responses; sent on every write as the server requires.
let csrfToken: string | null = null
export function setCsrfToken(token: string | null) {
  csrfToken = token
}

const csrf: Middleware = {
  onRequest({ request }) {
    if (csrfToken && request.method !== 'GET') request.headers.set('X-CSRF-Token', csrfToken)
    return request
  },
}

export const api = createClient<paths>({ baseUrl: '/', credentials: 'same-origin' })
api.use(csrf)

export type ApiError = { code: string; message: string; details?: unknown }
