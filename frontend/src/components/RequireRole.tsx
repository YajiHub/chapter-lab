import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../auth'
import { homeFor, type Role } from '../lib/roles'
import { Spinner } from './Spinner'

/** Signed out -> /signin (remembering where they were going); wrong role -> that role's home. */
export function RequireRole({ role }: { role: Role }) {
  const { user, isLoading } = useAuth()
  const location = useLocation()
  if (isLoading) return <Spinner center label="Loading your session…" />
  if (!user) return <Navigate to="/signin" replace state={{ from: location.pathname + location.search }} />
  if (user.role !== role) return <Navigate to={homeFor(user.role)} replace />
  return <Outlet />
}
