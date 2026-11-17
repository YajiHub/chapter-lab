import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, type ApiError } from '../api/client'
import { Button } from '../components/Button'
import { Field } from '../components/Field'
import { PageHeader } from '../components/PageHeader'
import { Spinner } from '../components/Spinner'
import { errorMessage, fieldErrors, type FieldErrors } from '../lib/errors'
import { buttonClass, inputClass, linkClass } from '../lib/styles'

const TITLE_MAX = 160
const NOTES_MAX = 6000

type Values = { title: string; notes: string }

export default function LessonForm() {
  const { lessonId } = useParams()

  const lesson = useQuery({
    queryKey: ['lessons', 'detail', lessonId],
    enabled: !!lessonId,
    retry: (count, err) => (err as { status?: number }).status !== 404 && count < 1,
    queryFn: async () => {
      const { data, error, response } = await api.GET('/api/v1/lessons/{lesson_id}', {
        params: { path: { lesson_id: lessonId! } },
      })
      if (error || !data) throw { ...(error as ApiError), status: response.status }
      return data
    },
  })

  if (!lessonId) return <LessonEditor initial={{ title: '', notes: '' }} />
  if (lesson.isPending) return <Spinner label="Loading lesson…" />
  if (lesson.isError) {
    const notFound = (lesson.error as { status?: number }).status === 404
    return (
      <>
        <PageHeader title={notFound ? 'Lesson not found' : 'Edit lesson'} />
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          <p>
            {notFound
              ? 'This lesson does not exist or was deleted.'
              : errorMessage(lesson.error, 'Could not load the lesson.')}
          </p>
          <div className="mt-3 flex gap-3">
            {!notFound && (
              <Button variant="secondary" onClick={() => lesson.refetch()}>
                Try again
              </Button>
            )}
            <Link to="/lessons" className={buttonClass('secondary')}>
              Back to lessons
            </Link>
          </div>
        </div>
      </>
    )
  }
  return <LessonEditor lessonId={lessonId} initial={{ title: lesson.data.title, notes: lesson.data.notes }} />
}

function validate({ title, notes }: Values): FieldErrors {
  const errors: FieldErrors = {}
  if (!title.trim()) errors.title = 'Enter a title.'
  else if (title.length > TITLE_MAX) errors.title = `Keep the title to ${TITLE_MAX} characters or fewer.`
  if (!notes.trim()) errors.notes = 'Paste the notes for this lesson.'
  else if (notes.length > NOTES_MAX)
    errors.notes = `Notes are limited to ${NOTES_MAX.toLocaleString()} characters. Pick a smaller section of the chapter and try again.`
  return errors
}

function LessonEditor({ lessonId, initial }: { lessonId?: string; initial: Values }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [values, setValues] = useState(initial)
  const [clientErrors, setClientErrors] = useState<FieldErrors>({})

  const save = useMutation({
    mutationFn: async (body: Values) => {
      const { error } = lessonId
        ? await api.PUT('/api/v1/lessons/{lesson_id}', { params: { path: { lesson_id: lessonId } }, body })
        : await api.POST('/api/v1/lessons', { body })
      if (error) throw error
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['lessons'] })
      navigate('/lessons')
    },
  })

  const serverErrors = save.isError ? fieldErrors(save.error) : {}
  const errors = { ...serverErrors, ...clientErrors }
  const notesOver = values.notes.length > NOTES_MAX

  function set(field: keyof Values, value: string) {
    setValues((v) => ({ ...v, [field]: value }))
    if (clientErrors[field])
      setClientErrors((prev) => {
        const next = { ...prev }
        delete next[field]
        return next
      })
  }

  function submit(e: FormEvent) {
    e.preventDefault()
    const found = validate(values)
    setClientErrors(found)
    if (Object.keys(found).length === 0) save.mutate({ title: values.title.trim(), notes: values.notes })
  }

  const hasFieldErrors = Object.keys(serverErrors).length > 0

  return (
    <>
      <PageHeader title={lessonId ? 'Edit lesson' : 'New lesson'} />
      <form onSubmit={submit} noValidate className="space-y-5 rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        {save.isError && !hasFieldErrors && (
          <p role="alert" className="rounded-md bg-red-50 p-3 text-sm text-red-800">
            {errorMessage(save.error, 'Could not save the lesson.')}
          </p>
        )}
        <Field
          id="title"
          label="Title"
          error={errors.title}
          hint={`${values.title.length} / ${TITLE_MAX} characters`}
        >
          {(aria) => (
            <input
              {...aria}
              type="text"
              required
              maxLength={TITLE_MAX}
              value={values.title}
              onChange={(e) => set('title', e.target.value)}
              className={inputClass}
            />
          )}
        </Field>
        <Field
          id="notes"
          label="Notes"
          error={errors.notes}
          hint={
            <span className={notesOver ? 'font-medium text-red-700' : undefined}>
              {values.notes.length.toLocaleString()} / {NOTES_MAX.toLocaleString()} characters
              {notesOver && ' — too long, pick a smaller section'}
            </span>
          }
        >
          {(aria) => (
            <textarea
              {...aria}
              required
              rows={14}
              value={values.notes}
              onChange={(e) => set('notes', e.target.value)}
              className={`${inputClass} font-mono text-sm`}
            />
          )}
        </Field>
        <div className="flex flex-wrap items-center gap-4">
          <Button type="submit" disabled={save.isPending}>
            {save.isPending ? 'Saving…' : 'Save lesson'}
          </Button>
          <Link to="/lessons" className={linkClass}>
            Cancel
          </Link>
          {save.isPending && (
            <span role="status" className="sr-only">
              Saving lesson
            </span>
          )}
        </div>
      </form>
    </>
  )
}
