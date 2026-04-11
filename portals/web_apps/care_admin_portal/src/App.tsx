import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from './components/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppointmentsPage } from './pages/AppointmentsPage'
import { ClaimsPage } from './pages/ClaimsPage'
import { DashboardPage } from './pages/DashboardPage'
import { MembersPage } from './pages/MembersPage'
import { SignInPage } from './pages/SignInPage'
import { StaffPage } from './pages/StaffPage'
import { VisitsPage } from './pages/VisitsPage'

function App() {
  return (
    <Routes>
      <Route path="/signin" element={<SignInPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/app" element={<DashboardPage />} />
          <Route path="/app/appointments" element={<AppointmentsPage />} />
          <Route path="/app/claims" element={<ClaimsPage />} />
          <Route path="/app/visits" element={<VisitsPage />} />
          <Route path="/app/members" element={<MembersPage />} />
          <Route path="/app/staff" element={<StaffPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  )
}

export default App
