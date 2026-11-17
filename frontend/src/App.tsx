import { useQuery } from '@tanstack/react-query'
import { api } from './api/client'

// Phase 0 placeholder: proves the typed client + proxy work. L4 replaces this with the router shell.
export default function App() {
  const health = useQuery({
    queryKey: ['health'],
    queryFn: async () => (await api.GET('/api/health')).data,
  })
  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="text-2xl font-semibold">ChapterLab</h1>
      <p className="mt-2 text-slate-600">
        API: {health.isLoading ? 'checking…' : (health.data?.status ?? 'unreachable')} · version{' '}
        {health.data?.version ?? '—'}
      </p>
    </main>
  )
}
