import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

const navItems = [
  { label: 'Appointments', to: '/app/appointments' },
  { label: 'Book Care', to: '/app/appointments/new' },
  { label: 'Profile', to: '/app/profile' },
  { label: 'Chat', to: '/app/chat' },
]

export function AppShell() {
  const { member, signout } = useAuth()
  const displayName = [member?.first_name, member?.last_name].filter(Boolean).join(' ') || 'Member'

  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div>
          <div className="brand-mark">IH</div>
          <p className="eyebrow">In-Home Care</p>
          <h1>{displayName}</h1>
          <p className="muted">Personalized care coordination at home.</p>
        </div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-pill ${isActive ? 'active' : ''}`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button type="button" className="secondary-button sidebar-signout" onClick={signout}>
          Sign out
        </button>
      </aside>
      <main className="content-area">
        <Outlet />
      </main>
    </div>
  )
}
