import { Link } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { buttonClass } from '../lib/styles'

export default function Dashboard() {
  return (
    <>
      <PageHeader title="Dashboard" />
      <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="font-semibold">Coming in Phase 2</h2>
        <p className="mt-2 text-slate-600">Saved packs and recent results will show up here.</p>
        <Link to="/lessons" className={buttonClass('primary', 'mt-4')}>
          Go to lessons
        </Link>
      </section>
    </>
  )
}
