import { NavLink, Outlet } from 'react-router-dom'

import { useAuth } from '../context/AuthContext'

const navItems = [
  { label: 'Appointments', to: '/app/appointments', icon: '🗓', meta: 'History & search' },
  { label: 'Book Care', to: '/app/appointments/new', icon: '＋', meta: 'Request new service' },
  { label: 'Profile', to: '/app/profile', icon: '👤', meta: 'Addresses & settings' },
  { label: 'Chat', to: '/app/chat', icon: '💬', meta: 'Care concierge' },
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
          <p className="muted sidebar-copy">Personalized care coordination with a clear, member-first experience.</p>
          <div className="member-status-card">
            <span className="status-dot" />
            <div>
              <strong>Portal active</strong>
              <p className="muted">Signed in as a member</p>
            </div>
          </div>
        </div>
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
          <p className="eyebrow">Member support</p>
          <p>Use chat for quick guidance, then review appointments and visit details in one place.</p>
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
