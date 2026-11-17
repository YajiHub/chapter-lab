import { useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth, type Role } from '../auth'
import { Button } from './Button'

const NAV: Record<Role, { to: string; label: string }[]> = {
  student: [
    { to: '/', label: 'Dashboard' },
    { to: '/lessons', label: 'Lessons' },
    { to: '/packs', label: 'Study packs' },
  ],
  admin: [{ to: '/admin', label: 'Administration' }],
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-md px-2 py-1 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 ${
    isActive ? 'bg-indigo-50 text-indigo-700' : 'text-slate-600 hover:text-slate-900'
  }`

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [signingOut, setSigningOut] = useState(false)

  async function signOut() {
    setSigningOut(true)
    try {
      await logout()
    } finally {
      setSigningOut(false)
      navigate('/signin', { replace: true })
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <a
        href="#main"
        className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:z-10 focus:rounded-md focus:bg-white focus:px-3 focus:py-2 focus:shadow"
      >
        Skip to content
      </a>
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3">
          <span className="text-lg font-semibold text-indigo-700">ChapterLab</span>
          {user && (
            <>
              <nav aria-label="Main" className="flex flex-wrap gap-1">
                {NAV[user.role].map((item) => (
                  <NavLink key={item.to} to={item.to} end className={navClass}>
                    {item.label}
                  </NavLink>
                ))}
              </nav>
              <div className="ml-auto flex items-center gap-3">
                <span className="max-w-[16rem] truncate text-sm text-slate-600">{user.email}</span>
                <Button variant="secondary" onClick={signOut} disabled={signingOut}>
                  {signingOut ? 'Signing out…' : 'Sign out'}
                </Button>
              </div>
            </>
          )}
        </div>
      </header>
      <main id="main" tabIndex={-1} className="mx-auto max-w-5xl px-4 py-8 focus:outline-none">
        <Outlet />
      </main>
    </div>
  )
}
