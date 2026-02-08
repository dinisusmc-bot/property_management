import { Routes, Route, Navigate } from 'react-router-dom'
import { Box } from '@mui/material'
import { useAuthStore } from './store/authStore'
import Layout from './components/Layout'
import Login from './pages/Login'
import HomePage from './pages/HomePage'
import QuoteLanding from './pages/QuoteLanding'
import DashboardPage from './pages/dashboard/DashboardPage'
import LeadsPage from './pages/leads/LeadsPage'
import LeadDetailPage from './pages/leads/LeadDetailPage'
import LeadFormPage from './pages/leads/LeadFormPage'
import VendorDashboard from './pages/VendorDashboard'
import VendorCharterDetail from './pages/VendorCharterDetail'
import DriverDashboard from './pages/driver/DriverDashboard'
import CharterList from './pages/charters/CharterList'
import CharterDetail from './pages/charters/CharterDetail'
import CharterCreate from './pages/charters/CharterCreate'
import ClientList from './pages/clients/ClientList'
import ClientDetail from './pages/clients/ClientDetail'
import ClientCreate from './pages/clients/ClientCreate'
import VendorList from './pages/vendors/VendorList'
import VendorDetail from './pages/vendors/VendorDetail'
import UserList from './pages/users/UserList'
import UserDetail from './pages/users/UserDetail'
import UserCreate from './pages/users/UserCreate'
import PaymentsList from './pages/payments/PaymentsList'
import PaymentDetail from './pages/payments/PaymentDetail'
import AccountsReceivable from './pages/payments/AccountsReceivable'
import AccountsPayable from './pages/payments/AccountsPayable'
import ChangeCasesPage from './pages/changes/ChangeCasesPage'
import ChangeCaseCreatePage from './pages/changes/ChangeCaseCreatePage'

// Protected route component
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore()
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

// Vendor route component - redirects vendors to vendor dashboard
function DashboardRoute() {
  const user = useAuthStore(state => state.user)
  if (user?.role === 'vendor') {
    return <Navigate to="/vendor" replace />
  }
  if (user?.role === 'driver') {
    return <Navigate to="/driver" replace />
  }
  return <DashboardPage />
}

// Non-vendor route component - redirects vendors and drivers trying to access admin pages
function NonVendorRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore(state => state.user)
  if (user?.role === 'vendor') {
    return <Navigate to="/vendor" replace />
  }
  if (user?.role === 'driver') {
    return <Navigate to="/driver" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Routes>
        {/* Public routes - no authentication required */}
        <Route path="/" element={<HomePage />} />
        <Route path="/home" element={<HomePage />} />
        <Route path="/quote" element={<QuoteLanding />} />
        <Route path="/login" element={<Login />} />
        
        {/* Protected routes - require authentication */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Layout>
                <DashboardRoute />
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/vendor"
          element={
            <ProtectedRoute>
              <Layout>
                <VendorDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/vendor/charter/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <VendorCharterDetail />
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/driver"
          element={
            <ProtectedRoute>
              <Layout>
                <DriverDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Charter routes - protected from vendors */}
        <Route
          path="/charters"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <CharterList />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/charters/new"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <CharterCreate />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/charters/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <CharterDetail />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />

        {/* Lead routes - protected from vendors */}
        <Route
          path="/leads"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <LeadsPage />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/leads/new"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <LeadFormPage />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/leads/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <LeadDetailPage />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/leads/:id/edit"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <LeadFormPage />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Client routes - protected from vendors */}
        <Route
          path="/clients"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <ClientList />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/clients/new"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <ClientCreate />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/clients/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <ClientDetail />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Vendor routes - protected from vendors */}
        <Route
          path="/vendors"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <VendorList />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/vendors/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <VendorDetail />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* User routes - protected from vendors */}
        <Route
          path="/users"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <UserList />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/users/new"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <UserCreate />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/users/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <UserDetail />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Payment routes - protected from vendors */}
        <Route
          path="/receivables"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <AccountsReceivable />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/payables"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <AccountsPayable />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/payments"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <PaymentsList />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/payments/:type/:id"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <PaymentDetail />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Change Management routes - protected from vendors */}
        <Route
          path="/changes"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <ChangeCasesPage />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        <Route
          path="/changes/new"
          element={
            <ProtectedRoute>
              <Layout>
                <NonVendorRoute>
                  <ChangeCaseCreatePage />
                </NonVendorRoute>
              </Layout>
            </ProtectedRoute>
          }
        />
        
        {/* Catch all - redirect to home for public or dashboard for authenticated */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Box>
  )
}

export default App
