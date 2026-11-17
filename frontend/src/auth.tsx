import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useContext, useMemo, type ReactNode } from 'react'
import { api, setCsrfToken } from './api/client'
import type { components } from './api/schema'

export type User = components['schemas']['UserOut']
export type { Role } from './lib/roles'

type AuthValue = {
  user: User | null
  isLoading: boolean
  /** Resolves with the signed-in user; rejects with the API error body. */
  login: (email: string, password: string) => Promise<User>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)
const ME_KEY = ['auth', 'me'] as const

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  const me = useQuery({
    queryKey: ME_KEY,
    retry: false,
    staleTime: Infinity,
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/auth/me')
      if (response.status === 401) {
        setCsrfToken(null)
        return null // signed out, not an error
      }
      if (error || !data) throw error ?? new Error('Could not load your session.')
      setCsrfToken(data.csrfToken)
      return data.user
    },
  })

  const login = useCallback(
    async (email: string, password: string) => {
      const { data, error } = await api.POST('/api/v1/auth/login', { body: { email, password } })
      if (error || !data) throw error ?? new Error('Sign in failed.')
      setCsrfToken(data.csrfToken)
      queryClient.setQueryData(ME_KEY, data.user)
      return data.user
    },
    [queryClient],
  )

  const logout = useCallback(async () => {
    try {
      await api.POST('/api/v1/auth/logout')
    } finally {
      setCsrfToken(null)
      queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== ME_KEY[0] })
      queryClient.setQueryData(ME_KEY, null)
    }
  }, [queryClient])

  const value = useMemo<AuthValue>(
    () => ({ user: me.data ?? null, isLoading: me.isPending, login, logout }),
    [me.data, me.isPending, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// oxlint-disable-next-line react/only-export-components -- hook lives beside its provider
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
