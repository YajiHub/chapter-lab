import { useMutation } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth'
import { homeFor } from '../lib/roles'
import { Button } from '../components/Button'
import { Field } from '../components/Field'
import { Spinner } from '../components/Spinner'
import { errorMessage } from '../lib/errors'
import { inputClass } from '../lib/styles'

export default function SignIn() {
  const { user, isLoading, login } = useAuth()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const mutation = useMutation({ mutationFn: () => login(email, password) })

  if (isLoading) return <Spinner center label="Loading your session…" />
  if (user) {
    const from = (location.state as { from?: string } | null)?.from
    return <Navigate to={from && from !== '/signin' ? from : homeFor(user.role)} replace />
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <div className="mx-auto max-w-sm">
      <h1 className="mb-6 text-2xl font-semibold">Sign in</h1>
      <form onSubmit={submit} noValidate className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        {mutation.isError && (
          <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-800">
            {errorMessage(mutation.error, 'Sign in failed. Please try again.')}
          </p>
        )}
        <Field id="email" label="Email">
          {(aria) => (
            <input
              {...aria}
              type="email"
              autoComplete="username"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
            />
          )}
        </Field>
        <Field id="password" label="Password">
          {(aria) => (
            <input
              {...aria}
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          )}
        </Field>
        <Button type="submit" className="w-full" disabled={mutation.isPending || !email || !password}>
          {mutation.isPending ? 'Signing in…' : 'Sign in'}
        </Button>
      </form>
    </div>
  )
}
