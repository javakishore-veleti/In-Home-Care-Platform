import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from './components/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppointmentDetailPage } from './pages/AppointmentDetailPage'
import { AppointmentsPage } from './pages/AppointmentsPage'
import { ClaimsPage } from './pages/ClaimsPage'
import { DashboardPage } from './pages/DashboardPage'
import { MemberDetailPage } from './pages/MemberDetailPage'
import { MembersPage } from './pages/MembersPage'
import { SignInPage } from './pages/SignInPage'
import { SlackIntegrationsPage } from './pages/SlackIntegrationsPage'
import { StaffPage } from './pages/StaffPage'
import { VisitDetailPage } from './pages/VisitDetailPage'
import { VisitsPage } from './pages/VisitsPage'

function App() {
  return (
    <Routes>
      <Route path="/signin" element={<SignInPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/app" element={<DashboardPage />} />
          <Route path="/app/appointments" element={<AppointmentsPage />} />
          <Route path="/app/appointments/:appointmentId" element={<AppointmentDetailPage />} />
          <Route path="/app/claims" element={<ClaimsPage />} />
          <Route path="/app/visits" element={<VisitsPage />} />
          <Route path="/app/visits/:visitId" element={<VisitDetailPage />} />
          <Route path="/app/members" element={<MembersPage />} />
          <Route path="/app/members/:memberId" element={<MemberDetailPage />} />
          <Route path="/app/staff" element={<StaffPage />} />
          <Route path="/app/slack-integrations" element={<SlackIntegrationsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  )
}

export default App
