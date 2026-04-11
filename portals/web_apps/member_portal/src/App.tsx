import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from './components/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { useAuth } from './context/AuthContext'
import { AppointmentDetailPage } from './pages/AppointmentDetailPage'
import { AppointmentsPage } from './pages/AppointmentsPage'
import { ChatPage } from './pages/ChatPage'
import { HomePage } from './pages/HomePage'
import { NewAppointmentPage } from './pages/NewAppointmentPage'
import { ProfilePage } from './pages/ProfilePage'
import { SignInPage } from './pages/SignInPage'
import { SignUpPage } from './pages/SignUpPage'

function App() {
  const { token } = useAuth()

  return (
    <Routes>
      <Route path="/" element={<PublicLayout><HomePage /></PublicLayout>} />
      <Route path="/signin" element={<PublicLayout><SignInPage /></PublicLayout>} />
      <Route path="/signup" element={<PublicLayout><SignUpPage /></PublicLayout>} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/app" element={<Navigate replace to="/app/appointments" />} />
          <Route path="/app/profile" element={<ProfilePage />} />
          <Route path="/app/appointments" element={<AppointmentsPage />} />
          <Route path="/app/appointments/new" element={<NewAppointmentPage />} />
          <Route path="/app/appointments/:appointmentId" element={<AppointmentDetailPage />} />
          <Route path="/app/chat" element={<ChatPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to={token ? '/app/appointments' : '/'} replace />} />
    </Routes>
  )
}

function PublicLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="public-shell">
      <header className="public-header">
        <div>
          <p className="eyebrow">In-Home Care</p>
          <h1>Member experience</h1>
        </div>
      </header>
      <main className="public-main">{children}</main>
    </div>
  )
}

export default App
