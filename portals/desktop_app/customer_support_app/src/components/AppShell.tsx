import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

const NAV = [
  { to: '/app', label: 'Cases', end: true },
  { to: '/app/members', label: 'Members' },
  { to: '/app/appointments', label: 'Appointments' },
  { to: '/app/visits', label: 'Visits' },
]

export function AppShell() {
  const { user, signout } = useAuth()
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-[#1A2B3C] text-white px-6 py-3 flex items-center gap-3">
        <img src="/logo.svg" alt="Logo" className="h-8 w-8" />
        <h1 className="text-lg font-bold">Customer Support</h1>
        <div className="flex-1" />
        <div className="text-sm flex items-center gap-3">
          <span className="text-white/80">{user?.email}</span>
          <span className="px-2 py-0.5 rounded-full bg-[#0D7377] text-xs uppercase tracking-wide">
            {user?.role ?? 'unknown'}
          </span>
          <button
            type="button"
            onClick={signout}
            className="px-3 py-1.5 rounded bg-white/10 hover:bg-white/20 text-xs font-semibold"
          >
            Sign out
          </button>
        </div>
      </header>
      <div className="flex flex-1">
        <aside className="w-56 bg-[#0D7377] text-white p-4 space-y-2">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block w-full text-left px-3 py-2 rounded font-medium text-sm text-white no-underline visited:text-white hover:text-white ${
                  isActive ? 'bg-[#084C4F]' : 'hover:bg-[#084C4F]/70'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </aside>
        <main className="flex-1 p-6 bg-[#F4F7FA]">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
