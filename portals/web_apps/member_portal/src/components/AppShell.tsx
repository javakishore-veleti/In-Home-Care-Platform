import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

const navItems = [
  { label: 'Appointments', to: '/app/appointments', icon: '○', meta: 'Search and review' },
  { label: 'Book Care', to: '/app/appointments/new', icon: '＋', meta: 'Request a new visit' },
  { label: 'Profile', to: '/app/profile', icon: '◇', meta: 'Addresses and details' },
  { label: 'Chat', to: '/app/chat', icon: '✦', meta: 'Member support' },
]

export function AppShell() {
  const { member, signout } = useAuth()
  const displayName = [member?.first_name, member?.last_name].filter(Boolean).join(' ') || 'Member'

  return (
    <div className="app-frame">
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="brand-mark">IH</div>
          <p className="eyebrow">In-Home Care</p>
          <h1>{displayName}</h1>
          <p className="muted sidebar-copy">A calmer member space for booking care, checking updates, and keeping household details current.</p>
          <div className="member-status-card">
            <span className="status-dot" />
            <div>
              <strong>Account active</strong>
              <p className="muted">You are signed in</p>
            </div>
          </div>
        </div>
        <div className="nav-section-label">Go to</div>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-pill ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span>
                <strong>{item.label}</strong>
                <small>{item.meta}</small>
              </span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-note">
          <p className="eyebrow">Need help?</p>
          <p>Start with appointments, then use chat if you need help finding visit updates or service details.</p>
        </div>
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
