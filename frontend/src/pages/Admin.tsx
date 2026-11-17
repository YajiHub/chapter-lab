import { PageHeader } from '../components/PageHeader'

export default function Admin() {
  return (
    <>
      <PageHeader title="Administration" />
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-semibold">Coming in Phase 2</h2>
        <p className="mt-2 text-slate-600">Account management and generation status will show up here.</p>
      </section>
    </>
  )
}
