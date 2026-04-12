import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

const NAV = [
  { to: '/app', label: 'Dashboard', end: true },
  { to: '/app/appointments', label: 'Appointments' },
  { to: '/app/claims', label: 'Slack Claims' },
  { to: '/app/visits', label: 'Visits' },
  { to: '/app/members', label: 'Members' },
  { to: '/app/staff', label: 'Staff' },
  { to: '/app/slack-integrations', label: 'Slack Integrations' },
  { to: '/app/knowledge-base', label: 'Knowledge Base' },
]

export function AppShell() {
  const { user, signout } = useAuth()

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-[#1A2B3C] text-white px-6 py-4 flex items-center gap-3 shadow-lg">
        <img src="/logo.svg" alt="Logo" className="h-10 w-10" />
        <h1 className="text-xl font-bold">Care Admin Portal</h1>
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
              style={{ color: '#ffffff', textDecoration: 'none' }}
              className={({ isActive }) =>
                `block w-full text-left px-3 py-2 rounded font-medium text-sm ${
                  isActive ? 'bg-[#084C4F]' : 'hover:bg-[#084C4F]/70'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </aside>
        <main className="flex-1 p-8 bg-[#F4F7FA]">
          <Outlet />
        </main>
      </div>
      <footer className="bg-[#1A2B3C] text-white text-center py-3 text-xs">
        Care Admin Portal &copy; 2026
      </footer>
    </div>
  )
}
