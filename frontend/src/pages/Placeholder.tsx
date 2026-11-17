import { PageHeader } from '../components/PageHeader'

/** Stand-in for screens owned by lane L5 (packs, workspace, results) until they land. */
export default function Placeholder({ title }: { title: string }) {
  return (
    <>
      <PageHeader title={title} />
      <p className="rounded-lg border border-slate-200 bg-white p-6 text-slate-600">Coming in Phase 2.</p>
    </>
  )
}
