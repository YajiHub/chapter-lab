import type { components } from '../api/schema'

export type Role = components['schemas']['UserOut']['role']

export function homeFor(role: Role) {
  return role === 'admin' ? '/admin' : '/'
}
