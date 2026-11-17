import { Link } from 'react-router-dom'
import { linkClass } from '../lib/styles'

export default function NotFound() {
  return (
    <div className="py-12 text-center">
      <h1 className="text-2xl font-semibold">Page not found</h1>
      <p className="mt-2 text-slate-600">That page does not exist.</p>
      <Link to="/" className={`${linkClass} mt-4 inline-block`}>
        Go home
      </Link>
    </div>
  )
}
