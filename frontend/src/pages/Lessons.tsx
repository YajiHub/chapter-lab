import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { Button } from '../components/Button'
import { EmptyState } from '../components/EmptyState'
import { PageHeader } from '../components/PageHeader'
import { Spinner } from '../components/Spinner'
import { errorMessage } from '../lib/errors'
import { buttonClass, inputClass, linkClass } from '../lib/styles'

type Sort = 'newest' | 'oldest'

const dateFmt = new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' })

export default function Lessons() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const q = params.get('q') ?? ''
  const sort: Sort = params.get('sort') === 'oldest' ? 'oldest' : 'newest'

  function update(next: { page?: number; q?: string; sort?: Sort }) {
    const merged = { page, q, sort, ...next }
    const out = new URLSearchParams()
    if (merged.page > 1) out.set('page', String(merged.page))
    if (merged.q) out.set('q', merged.q)
    if (merged.sort !== 'newest') out.set('sort', merged.sort)
    setParams(out)
  }

  // Search box: local text, pushed to the URL after 300ms idle (or on Enter).
  const [search, setSearch] = useState(q)
  const [syncedQ, setSyncedQ] = useState(q)
  if (syncedQ !== q) {
    // URL changed under us (back/forward, clear search): follow it.
    setSyncedQ(q)
    setSearch(q)
  }
  useEffect(() => {
    const next = search.trim()
    if (next === q) return
    const t = setTimeout(
      () =>
        setParams((prev) => {
          const out = new URLSearchParams(prev)
          out.delete('page')
          if (next) out.set('q', next)
          else out.delete('q')
          return out
        }),
      300,
    )
    return () => clearTimeout(t)
  }, [search, q, setParams])

  const queryClient = useQueryClient()
  const lessons = useQuery({
    queryKey: ['lessons', { page, q, sort }],
    placeholderData: keepPreviousData,
    queryFn: async () => {
      const { data, error } = await api.GET('/api/v1/lessons', {
        params: { query: { page, sort, q: q || undefined } },
      })
      if (error || !data) throw error ?? new Error('Could not load lessons.')
      return data
    },
  })

  const remove = useMutation({
    mutationFn: async (lessonId: string) => {
      const { error } = await api.DELETE('/api/v1/lessons/{lesson_id}', {
        params: { path: { lesson_id: lessonId } },
      })
      if (error) throw error
    },
    onSuccess: () => {
      // Deleting the last row of a later page: step back so the user is not left on an empty page.
      if (lessons.data?.items.length === 1 && page > 1) update({ page: page - 1 })
      return queryClient.invalidateQueries({ queryKey: ['lessons'] })
    },
  })

  function confirmDelete(id: string, title: string) {
    if (window.confirm(`Delete "${title}"? This cannot be undone.`)) remove.mutate(id)
  }

  const newButton = (
    <Link to="/lessons/new" className={buttonClass('primary')}>
      New lesson
    </Link>
  )

  const data = lessons.data
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.pageSize)) : 1

  return (
    <>
      <PageHeader title="Lessons" actions={newButton} />

      <form
        role="search"
        className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end"
        onSubmit={(e) => {
          e.preventDefault()
          update({ q: search.trim(), page: 1 })
        }}
      >
        <div className="flex-1 space-y-1">
          <label htmlFor="lesson-search" className="block text-sm font-medium text-slate-800">
            Search lessons
          </label>
          <input
            id="lesson-search"
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by title"
            className={inputClass}
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="lesson-sort" className="block text-sm font-medium text-slate-800">
            Sort
          </label>
          <select
            id="lesson-sort"
            value={sort}
            onChange={(e) => update({ sort: e.target.value as Sort, page: 1 })}
            className={inputClass}
          >
            <option value="newest">Newest</option>
            <option value="oldest">Oldest</option>
          </select>
        </div>
      </form>

      {remove.isError && (
        <p role="alert" className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-800">
          {errorMessage(remove.error, 'Could not delete the lesson.')}
        </p>
      )}

      {lessons.isPending ? (
        <Spinner label="Loading lessons…" />
      ) : lessons.isError ? (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          <p>{errorMessage(lessons.error, 'Could not load lessons.')}</p>
          <Button variant="secondary" className="mt-3" onClick={() => lessons.refetch()}>
            Try again
          </Button>
        </div>
      ) : data!.items.length === 0 ? (
        q ? (
          <EmptyState title={`No lessons match "${q}".`}>
            <Button variant="secondary" onClick={() => update({ q: '', page: 1 })}>
              Clear search
            </Button>
          </EmptyState>
        ) : page > 1 ? (
          <EmptyState title="This page is empty.">
            <Button variant="secondary" onClick={() => update({ page: 1 })}>
              Go to page 1
            </Button>
          </EmptyState>
        ) : (
          <EmptyState title="No lessons yet">{newButton}</EmptyState>
        )
      ) : (
        <>
          <ul className="divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white" aria-busy={lessons.isFetching}>
            {data!.items.map((lesson) => (
              <li key={lesson.id} className="flex flex-wrap items-center gap-3 px-4 py-3">
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{lesson.title}</p>
                  <p className="text-sm text-slate-500">
                    Updated <time dateTime={lesson.updatedAt}>{dateFmt.format(new Date(lesson.updatedAt))}</time>
                  </p>
                </div>
                <Link to={`/lessons/${lesson.id}/edit`} className={linkClass} aria-label={`Edit ${lesson.title}`}>
                  Edit
                </Link>
                <Button
                  variant="danger"
                  onClick={() => confirmDelete(lesson.id, lesson.title)}
                  disabled={remove.isPending && remove.variables === lesson.id}
                  aria-label={`Delete ${lesson.title}`}
                >
                  Delete
                </Button>
              </li>
            ))}
          </ul>
          <nav aria-label="Pagination" className="mt-4 flex items-center justify-between gap-3">
            <Button variant="secondary" disabled={page <= 1} onClick={() => update({ page: page - 1 })}>
              Previous
            </Button>
            <p role="status" className="text-sm text-slate-600">
              Page {page} of {totalPages}
            </p>
            <Button variant="secondary" disabled={page >= totalPages} onClick={() => update({ page: page + 1 })}>
              Next
            </Button>
          </nav>
        </>
      )}
    </>
  )
}
