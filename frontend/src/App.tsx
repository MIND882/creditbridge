import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Landing from './pages/Landing'
import Register from './pages/Register'
import ConsentFlow from './pages/ConsentFlow'
import Dashboard, { DashboardShell } from './pages/Dashboard'
import InvoiceManager from './pages/InvoiceManager'
import CreditScore from './pages/CreditScore'
import LoanOffers from './pages/LoanOffers'
import FinancialStatements from './pages/FinancialStatements'
import DocumentVault from './pages/DocumentVault'
import ProfileSetup from './pages/ProfileSetup'
import LoanApplication from './pages/LoanApplication'
import { useAuthStore } from './store/authStore'

// ✅ Tumhara original auth check — s.token — bilkul sahi
function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token)
  return token ? <>{children}</> : <Navigate to="/" />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes — same as before */}
        <Route path="/" element={<Landing />} />
        <Route path="/register" element={<Register />} />
        <Route path="/consent" element={
          <PrivateRoute><ConsentFlow /></PrivateRoute>
        } />

        {/* Dashboard — DashboardShell = Sidebar + <Outlet /> */}
        {/* Sab /dashboard/* pages sidebar ke saath render honge */}
        <Route path="/dashboard" element={
          <PrivateRoute><DashboardShell /></PrivateRoute>
        }>
          {/* /dashboard → home */}
          <Route index             element={<Dashboard />} />

          {/* /dashboard/invoices */}
          <Route path="invoices"   element={<InvoiceManager />} />

          {/* /dashboard/score */}
          <Route path="score"      element={<CreditScore />} />

          {/* /dashboard/loans */}
          <Route path="loans"      element={<LoanOffers />} />

          {/* /dashboard/apply */}
          <Route path="apply"      element={<LoanApplication />} />

          {/* /dashboard/statements */}
          <Route path="statements" element={<FinancialStatements />} />

          {/* /dashboard/documents */}
          <Route path="documents"  element={<DocumentVault />} />

          {/* /dashboard/profile */}
          <Route path="profile"    element={<ProfileSetup />} />
        </Route>

        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}