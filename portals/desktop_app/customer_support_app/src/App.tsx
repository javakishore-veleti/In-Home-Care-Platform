import { Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from './components/AppShell'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AppointmentsPage } from './pages/AppointmentsPage'
import { CasesPage } from './pages/CasesPage'
import { MembersPage } from './pages/MembersPage'
import { SignInPage } from './pages/SignInPage'
import { VisitsPage } from './pages/VisitsPage'

function App() {
  return (
    <Routes>
      <Route path="/signin" element={<SignInPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route path="/app" element={<CasesPage />} />
          <Route path="/app/members" element={<MembersPage />} />
          <Route path="/app/appointments" element={<AppointmentsPage />} />
          <Route path="/app/visits" element={<VisitsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/app" replace />} />
    </Routes>
  )
}

export default App
