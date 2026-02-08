# Phase 7: Client/Vendor Portals & Advanced Features
## Duration: 4 weeks | Priority: Medium

[← Back to Implementation Plan](README.md) | [← Phase 6](phase_6.md)

---

## Overview

**Goal**: Build separate client and vendor self-service portals, add communication system, enhance document management, and polish the entire application.

**Business Impact**: High - Enables client/vendor self-service, reducing admin workload. Completes the application with advanced features.

**Dependencies**:
- Backend Portal Service (Port 8000-8002) ✅ Ready
- Backend Communication Service (Port 8014) ✅ Ready
- Backend Documents Service (Port 8005) ✅ Ready
- **Phases 1-6 complete and E2E tested** ⚠️ Critical prerequisite

**Team Allocation**:
- **Senior Dev** (4 weeks): Portal authentication, bidding workflows, WebSocket integration
- **Junior Dev** (4 weeks): Portal UI, document management, mobile optimization

**⚠️ Critical Note**: This phase should only begin AFTER the admin portal (Phases 1-6) is fully implemented and tested end-to-end. The self-service portals reuse components from Phase 3 but with restricted permissions.

---

## Weeks 1-2: Client & Vendor Self-Service Portals

### Feature 7.0: Client Self-Service Portal

**Estimated Time**: 1 week | **Developer**: Senior Dev + Junior Dev

**Goal**: Create separate client portal where clients can log in, view their trips, make payments, and manage their account.

**Important**: This reuses many components from Phase 3 (ClientTripsTab, ClientPaymentsTab) but with restricted access and client-only authentication.

---

#### Task 7.0.1: Client Portal Layout (3 hours)

Create `frontend/src/layouts/ClientPortalLayout.tsx`:

```typescript
import { useState } from 'react'
import { useNavigate, Outlet } from 'react-router-dom'
import {
  Box,
  AppBar,
  Toolbar,
  Typography,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  useTheme,
  useMediaQuery
} from '@mui/material'
import {
  Menu as MenuIcon,
  DirectionsBus as TripIcon,
  Receipt as InvoiceIcon,
  Payment as PaymentIcon,
  Description as QuoteIcon,
  AccountCircle as ProfileIcon,
  Logout as LogoutIcon
} from '@mui/icons-material'
import { useAuthStore } from '@/stores/authStore'

const drawerWidth = 240

export default function ClientPortalLayout() {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [mobileOpen, setMobileOpen] = useState(false)
  
  const handleLogout = () => {
    logout()
    navigate('/client-login')
  }
  
  const menuItems = [
    { text: 'My Trips', icon: <TripIcon />, path: '/client-portal' },
    { text: 'Get Quote', icon: <QuoteIcon />, path: '/client-portal/quote' },
    { text: 'Payments', icon: <PaymentIcon />, path: '/client-portal/payments' },
    { text: 'Invoices', icon: <InvoiceIcon />, path: '/client-portal/invoices' },
    { text: 'Profile', icon: <ProfileIcon />, path: '/client-portal/profile' },
  ]
  
  const drawer = (
    <Box>
      <Toolbar sx={{ bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h6" noWrap>
          Client Portal
        </Typography>
      </Toolbar>
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton onClick={() => navigate(item.path)}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
        <ListItem disablePadding>
          <ListItemButton onClick={handleLogout}>
            <ListItemIcon><LogoutIcon /></ListItemIcon>
            <ListItemText primary="Logout" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  )
  
  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { md: `calc(100% - ${drawerWidth}px)` },
          ml: { md: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          {isMobile && (
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setMobileOpen(!mobileOpen)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" noWrap sx={{ flexGrow: 1 }}>
            Welcome, {user?.name}
          </Typography>
        </Toolbar>
      </AppBar>
      
      <Box
        component="nav"
        sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}
      >
        {isMobile ? (
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={() => setMobileOpen(false)}
            ModalProps={{ keepMounted: true }}
            sx={{ '& .MuiDrawer-paper': { width: drawerWidth } }}
          >
            {drawer}
          </Drawer>
        ) : (
          <Drawer
            variant="permanent"
            sx={{ '& .MuiDrawer-paper': { width: drawerWidth } }}
          >
            {drawer}
          </Drawer>
        )}
      </Box>
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { md: `calc(100% - ${drawerWidth}px)` },
          mt: 8
        }}
      >
        <Outlet />
      </Box>
    </Box>
  )
}
```

---

#### Task 7.0.2: Client Login Page (2 hours)

Create `frontend/src/pages/client-portal/ClientLogin.tsx`:

```typescript
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Link,
  Alert
} from '@mui/material'
import { Login as LoginIcon } from '@mui/icons-material'
import api from '@/services/api'
import { useAuthStore } from '@/stores/authStore'

const loginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function ClientLogin() {
  const navigate = useNavigate()
  const { setAuth } = useAuthStore()
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  })
  
  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    setError('')
    
    try {
      const response = await api.post('/api/v1/auth/client-login', data)
      setAuth(response.data.token, response.data.user)
      navigate('/client-portal')
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed')
    } finally {
      setLoading(false)
    }
  }
  
  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
      }}
    >
      <Paper sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Typography variant="h4" align="center" gutterBottom>
          Client Portal
        </Typography>
        <Typography variant="body2" color="textSecondary" align="center" sx={{ mb: 3 }}>
          Sign in to view your trips and manage your account
        </Typography>
        
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        
        <Box component="form" onSubmit={handleSubmit(onSubmit)}>
          <TextField
            {...register('email')}
            label="Email"
            fullWidth
            margin="normal"
            error={!!errors.email}
            helperText={errors.email?.message}
          />
          <TextField
            {...register('password')}
            label="Password"
            type="password"
            fullWidth
            margin="normal"
            error={!!errors.password}
            helperText={errors.password?.message}
          />
          <Button
            type="submit"
            variant="contained"
            fullWidth
            size="large"
            startIcon={<LoginIcon />}
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </Button>
          
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Link href="/quote" variant="body2">
              Need an account? Get a quote
            </Link>
          </Box>
        </Box>
      </Paper>
    </Box>
  )
}
```

---

#### Task 7.0.3: Client Trips Page (2 hours)

Create `frontend/src/pages/client-portal/ClientTrips.tsx` (reuses Phase 3 components):

```typescript
import { useState } from 'react'
import {
  Box,
  Paper,
  Tabs,
  Tab,
  Typography
} from '@mui/material'
import ClientTripsTab from '@/features/clients/components/ClientTripsTab'
import { useAuthStore } from '@/stores/authStore'

export default function ClientTrips() {
  const { user } = useAuthStore()
  const [tab, setTab] = useState(0)
  
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        My Trips
      </Typography>
      
      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="Upcoming" />
          <Tab label="Past" />
          <Tab label="Quotes" />
        </Tabs>
      </Paper>
      
      <Paper sx={{ p: 2 }}>
        {user && <ClientTripsTab clientId={user.client_id} />}
      </Paper>
    </Box>
  )
}
```

---

#### Task 7.0.4: Vendor Portal (1 week)

Similar structure for vendor portal:
- `VendorPortalLayout.tsx`
- `VendorLogin.tsx`
- `VendorBidding.tsx` - Reuse bidding components from Phase 3
- `VendorCOI.tsx` - Reuse COI management from Phase 3
- `VendorTrips.tsx` - View assigned trips

**Steps**:
1. Create vendor portal layout (same pattern as client)
2. Create vendor login page
3. Create vendor bidding page (view opportunities, submit bids)
4. Create vendor COI upload page (vendor uploads their own COI)
5. Create vendor trips page (view assigned trips)
6. Add routes to `App.tsx`

---

#### Task 7.0.5: Add Portal Routes (30 minutes)

Update `frontend/src/App.tsx`:

```typescript
import ClientLogin from './pages/client-portal/ClientLogin'
import ClientPortalLayout from './layouts/ClientPortalLayout'
import ClientTrips from './pages/client-portal/ClientTrips'
import VendorLogin from './pages/vendor-portal/VendorLogin'
import VendorPortalLayout from './layouts/VendorPortalLayout'

// Add routes
<Route path="/client-login" element={<ClientLogin />} />
<Route path="/client-portal" element={<ClientPortalLayout />}>
  <Route index element={<ClientTrips />} />
  <Route path="quote" element={<ClientQuote />} />
  <Route path="payments" element={<ClientPayments />} />
  <Route path="invoices" element={<ClientInvoices />} />
  <Route path="profile" element={<ClientProfile />} />
</Route>

<Route path="/vendor-login" element={<VendorLogin />} />
<Route path="/vendor-portal" element={<VendorPortalLayout />}>
  <Route index element={<VendorTrips />} />
  <Route path="bidding" element={<VendorBidding />} />
  <Route path="coi" element={<VendorCOI />} />
  <Route path="profile" element={<VendorProfile />} />
</Route>
```

---

**Testing Checklist for Portals**:
- [ ] Client login works
- [ ] Client can view their trips only
- [ ] Client can view payment history
- [ ] Client portal layout responsive
- [ ] Vendor login works
- [ ] Vendor can view bidding opportunities
- [ ] Vendor can submit bids
- [ ] Vendor can upload COI
- [ ] Vendor can view assigned trips only
- [ ] Permissions enforced (clients can't see other clients' data)
- [ ] Logout works for both portals

---

## Weeks 3-4: Communication System, Documents & Polish

### Feature 7.1: Notification Center

**Estimated Time**: 2 days

#### Step-by-Step Implementation

**Task 7.1.1: Install WebSocket Library** (15 minutes)

```bash
cd frontend
npm install socket.io-client
```

**Task 7.1.2: Create WebSocket Service** (2 hours)

Create `frontend/src/services/websocket.ts`:

```typescript
import { io, Socket } from 'socket.io-client'
import { useAuthStore } from '@/stores/authStore'

class WebSocketService {
  private socket: Socket | null = null
  
  connect() {
    const { token } = useAuthStore.getState()
    
    this.socket = io('ws://localhost:8080', {
      auth: { token },
      transports: ['websocket']
    })
    
    this.socket.on('connect', () => {
      console.log('WebSocket connected')
    })
    
    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })
    
    this.socket.on('error', (error) => {
      console.error('WebSocket error:', error)
    })
  }
  
  disconnect() {
    if (this.socket) {
      this.socket.disconnect()
      this.socket = null
    }
  }
  
  on(event: string, callback: (data: any) => void) {
    if (this.socket) {
      this.socket.on(event, callback)
    }
  }
  
  off(event: string, callback?: (data: any) => void) {
    if (this.socket) {
      this.socket.off(event, callback)
    }
  }
  
  emit(event: string, data: any) {
    if (this.socket) {
      this.socket.emit(event, data)
    }
  }
}

export const wsService = new WebSocketService()
```

**Task 7.1.3: Create Notification Types** (30 minutes)

Create `frontend/src/features/notifications/types/notification.types.ts`:

```typescript
export interface Notification {
  id: number
  user_id: number
  type: 'charter_update' | 'payment_received' | 'change_request' | 'new_lead' | 'system'
  title: string
  message: string
  link: string | null
  is_read: boolean
  created_at: string
}
```

**Task 7.1.4: Create Notification Center** (4 hours)

Create `frontend/src/features/notifications/components/NotificationCenter.tsx`:

```typescript
import { useState, useEffect } from 'react'
import {
  IconButton,
  Badge,
  Menu,
  MenuItem,
  ListItemText,
  ListItemIcon,
  Typography,
  Box,
  Divider,
  Button
} from '@mui/material'
import {
  Notifications as NotificationIcon,
  Info as InfoIcon,
  CheckCircle as ReadIcon
} from '@mui/icons-material'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import api from '@/services/api'
import { wsService } from '@/services/websocket'
import { Notification } from '../types/notification.types'
import { formatDistanceToNow } from 'date-fns'

export default function NotificationCenter() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  
  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: async () => {
      const response = await api.get<Notification[]>('/api/v1/notifications')
      return response.data
    }
  })
  
  const markAsReadMutation = useMutation({
    mutationFn: (id: number) => api.patch(`/api/v1/notifications/${id}/read`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    }
  })
  
  const markAllAsReadMutation = useMutation({
    mutationFn: () => api.post('/api/v1/notifications/mark-all-read'),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      toast.success('All notifications marked as read')
    }
  })
  
  useEffect(() => {
    // Connect to WebSocket for real-time notifications
    wsService.connect()
    
    wsService.on('notification', (data: Notification) => {
      queryClient.setQueryData(['notifications'], (old: Notification[] = []) => [data, ...old])
      toast(data.message, {
        icon: <NotificationIcon />,
        duration: 5000
      })
    })
    
    return () => {
      wsService.off('notification')
    }
  }, [queryClient])
  
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }
  
  const handleClose = () => {
    setAnchorEl(null)
  }
  
  const handleNotificationClick = (notification: Notification) => {
    markAsReadMutation.mutate(notification.id)
    handleClose()
    
    if (notification.link) {
      navigate(notification.link)
    }
  }
  
  const unreadCount = notifications?.filter((n) => !n.is_read).length || 0
  
  return (
    <>
      <IconButton color="inherit" onClick={handleClick}>
        <Badge badgeContent={unreadCount} color="error">
          <NotificationIcon />
        </Badge>
      </IconButton>
      
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: { width: 400, maxHeight: 500 }
        }}
      >
        <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6">Notifications</Typography>
          {unreadCount > 0 && (
            <Button
              size="small"
              startIcon={<ReadIcon />}
              onClick={() => markAllAsReadMutation.mutate()}
            >
              Mark all read
            </Button>
          )}
        </Box>
        
        <Divider />
        
        {notifications && notifications.length === 0 ? (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="textSecondary">No notifications</Typography>
          </Box>
        ) : (
          notifications?.map((notification) => (
            <MenuItem
              key={notification.id}
              onClick={() => handleNotificationClick(notification)}
              sx={{
                backgroundColor: notification.is_read ? 'transparent' : 'action.hover',
                borderLeft: notification.is_read ? 'none' : '3px solid primary.main'
              }}
            >
              <ListItemIcon>
                <InfoIcon color={notification.is_read ? 'disabled' : 'primary'} />
              </ListItemIcon>
              <ListItemText
                primary={notification.title}
                secondary={
                  <>
                    <Typography variant="body2" component="span">
                      {notification.message}
                    </Typography>
                    <br />
                    <Typography variant="caption" color="textSecondary">
                      {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                    </Typography>
                  </>
                }
              />
            </MenuItem>
          ))
        )}
      </Menu>
    </>
  )
}
```

**Task 7.1.5: Add to Layout** (30 minutes)

Update `frontend/src/components/Layout.tsx`:

```typescript
import NotificationCenter from '@/features/notifications/components/NotificationCenter'

// Add to AppBar Toolbar
<NotificationCenter />
```

**Testing Checklist**:
- [ ] Notification center displays
- [ ] Badge shows unread count
- [ ] Menu opens/closes
- [ ] Real-time notifications received
- [ ] Toast shows for new notifications
- [ ] Mark as read works
- [ ] Mark all read works
- [ ] Navigation on click works
- [ ] WebSocket connects/disconnects

---

### Feature 7.2: Document Preview

**Estimated Time**: 2 days

#### Implementation Tasks

**Task 7.2.1: Install PDF Library** (15 minutes)

```bash
cd frontend
npm install react-pdf pdfjs-dist
npm install --save-dev @types/react-pdf
```

**Task 7.2.2: Create Document Viewer** (3 hours)

Create `frontend/src/features/documents/components/DocumentViewer.tsx`:

```typescript
import { useState } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  IconButton,
  Typography
} from '@mui/material'
import {
  ZoomIn as ZoomInIcon,
  ZoomOut as ZoomOutIcon,
  Download as DownloadIcon,
  Close as CloseIcon
} from '@mui/icons-material'

// Configure worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`

interface DocumentViewerProps {
  open: boolean
  onClose: () => void
  fileUrl: string
  fileName: string
}

export default function DocumentViewer({ open, onClose, fileUrl, fileName }: DocumentViewerProps) {
  const [numPages, setNumPages] = useState<number>(0)
  const [pageNumber, setPageNumber] = useState(1)
  const [scale, setScale] = useState(1.0)
  
  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
  }
  
  const handleDownload = () => {
    const link = document.createElement('a')
    link.href = fileUrl
    link.download = fileName
    link.click()
  }
  
  const isPdf = fileName.toLowerCase().endsWith('.pdf')
  
  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth>
      <DialogTitle>
        <Box display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="h6">{fileName}</Typography>
          <Box>
            {isPdf && (
              <>
                <IconButton onClick={() => setScale(s => Math.max(0.5, s - 0.1))}>
                  <ZoomOutIcon />
                </IconButton>
                <IconButton onClick={() => setScale(s => Math.min(2.0, s + 0.1))}>
                  <ZoomInIcon />
                </IconButton>
              </>
            )}
            <IconButton onClick={handleDownload}>
              <DownloadIcon />
            </IconButton>
            <IconButton onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: 400,
            backgroundColor: '#f5f5f5',
            p: 2
          }}
        >
          {isPdf ? (
            <Document file={fileUrl} onLoadSuccess={onDocumentLoadSuccess}>
              <Page pageNumber={pageNumber} scale={scale} />
            </Document>
          ) : (
            <img src={fileUrl} alt={fileName} style={{ maxWidth: '100%', maxHeight: '70vh' }} />
          )}
        </Box>
        
        {isPdf && numPages > 0 && (
          <Box display="flex" justifyContent="center" alignItems="center" gap={2} mt={2}>
            <Button
              size="small"
              disabled={pageNumber <= 1}
              onClick={() => setPageNumber(p => p - 1)}
            >
              Previous
            </Button>
            <Typography>
              Page {pageNumber} of {numPages}
            </Typography>
            <Button
              size="small"
              disabled={pageNumber >= numPages}
              onClick={() => setPageNumber(p => p + 1)}
            >
              Next
            </Button>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  )
}
```

**Testing Checklist**:
- [ ] PDF viewer displays
- [ ] Image viewer displays
- [ ] Zoom in/out works
- [ ] Page navigation works
- [ ] Download button works
- [ ] Close button works

---

## Week 2: Mobile Optimization & Polish

### Feature 7.3: PWA Setup

**Estimated Time**: 2 days

#### Implementation Tasks

**Task 7.3.1: Add PWA Dependencies** (30 minutes)

```bash
cd frontend
npm install vite-plugin-pwa workbox-window
```

**Task 7.3.2: Configure PWA** (2 hours)

Update `frontend/vite.config.ts`:

```typescript
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'Athena Charter Management',
        short_name: 'Athena',
        description: 'Charter management system for transportation companies',
        theme_color: '#1976d2',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 // 1 hour
              }
            }
          }
        ]
      }
    })
  ]
})
```

**Task 7.3.3: Mobile Responsiveness Review** (3 hours)

- Review all components for mobile responsiveness
- Test on various screen sizes (320px, 768px, 1024px, 1920px)
- Ensure tables collapse properly on mobile
- Verify drawer navigation works on mobile
- Test forms on mobile devices
- Ensure touch targets are at least 48x48px

**Task 7.3.4: Performance Optimization** (2 hours)

Create `frontend/src/utils/lazyLoad.ts`:

```typescript
import { lazy } from 'react'

// Lazy load heavy components
export const CharterList = lazy(() => import('@/pages/charters/CharterList'))
export const CharterDetail = lazy(() => import('@/pages/charters/CharterDetail'))
export const DispatchBoard = lazy(() => import('@/features/dispatch/components/DispatchBoard'))
export const RevenueDashboard = lazy(() => import('@/features/analytics/components/RevenueDashboard'))
```

Update `frontend/src/App.tsx`:

```typescript
import { Suspense } from 'react'
import { CircularProgress, Box } from '@mui/material'
import * as LazyComponents from './utils/lazyLoad'

const LoadingFallback = () => (
  <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
    <CircularProgress />
  </Box>
)

// Wrap routes with Suspense
<Route
  path="/charters"
  element={
    <ProtectedRoute>
      <Layout>
        <Suspense fallback={<LoadingFallback />}>
          <LazyComponents.CharterList />
        </Suspense>
      </Layout>
    </ProtectedRoute>
  }
/>
```

**Task 7.3.5: Final UI Polish** (2 hours)

Checklist:
- [ ] Consistent spacing (8px grid)
- [ ] Consistent typography
- [ ] Color palette consistent
- [ ] Button styles consistent
- [ ] Form field styles consistent
- [ ] Loading states everywhere
- [ ] Empty states everywhere
- [ ] Error states everywhere
- [ ] Success feedback (toasts)
- [ ] Hover states on interactive elements
- [ ] Focus states for accessibility
- [ ] Proper loading skeletons
- [ ] Smooth transitions
- [ ] Proper z-index layering

---

### Feature 7.4: Final Testing & Documentation

**Estimated Time**: 2 days

#### Tasks

**Task 7.4.1: Cross-Browser Testing** (3 hours)

Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)
- [ ] Mobile Safari (iOS)
- [ ] Mobile Chrome (Android)

**Task 7.4.2: E2E Testing Critical Flows** (3 hours)

Manual testing of:
- [ ] Login flow
- [ ] Create charter (full workflow)
- [ ] Lead to quote conversion
- [ ] Payment processing
- [ ] Change case creation
- [ ] Vendor assignment
- [ ] Client portal access
- [ ] Report generation
- [ ] QuickBooks sync
- [ ] Notification delivery

**Task 7.4.3: Update Documentation** (2 hours)

- [ ] Update README with new features
- [ ] Document environment variables
- [ ] Document API endpoints used
- [ ] Document component hierarchy
- [ ] Create user guide (basic)
- [ ] Document deployment steps
- [ ] Document troubleshooting tips

---

## Deliverables Checklist

- [ ] Notification center with badge
- [ ] Real-time WebSocket notifications
- [ ] Toast notifications
- [ ] Mark read functionality
- [ ] Email template editor
- [ ] Communication log
- [ ] Document viewer (PDF + images)
- [ ] Zoom controls
- [ ] Page navigation
- [ ] PWA configured
- [ ] Service worker registered
- [ ] App installable
- [ ] Offline support (basic)
- [ ] Mobile responsive (all pages)
- [ ] Performance optimized
- [ ] Lazy loading implemented
- [ ] UI polish complete
- [ ] Cross-browser tested
- [ ] E2E flows tested
- [ ] Documentation updated

---

## Project Completion Criteria

### Code Quality
- [ ] All TypeScript errors resolved
- [ ] No console.error in production
- [ ] All components < 300 lines
- [ ] All files follow naming conventions
- [ ] No hardcoded values (use env vars)
- [ ] All API calls have error handling
- [ ] All forms have validation

### Functionality
- [ ] All 7 phases complete
- [ ] All features from gap analysis implemented
- [ ] All backend APIs integrated
- [ ] All user roles working
- [ ] All workflows functional

### User Experience
- [ ] Fast load times (< 3s initial)
- [ ] Smooth interactions
- [ ] Clear feedback on actions
- [ ] Intuitive navigation
- [ ] Mobile-friendly
- [ ] Accessible (WCAG AA)

### Testing
- [ ] All critical paths tested manually
- [ ] No breaking bugs
- [ ] Performance acceptable
- [ ] Cross-browser compatible

### Documentation
- [ ] README updated
- [ ] API endpoints documented
- [ ] Component docs added
- [ ] Deployment guide complete

---

## Handoff Notes

**For Junior Developers:**
- Follow the 3-step implementation flow from README.md
- Reference code patterns for consistency
- Test each feature thoroughly before marking complete
- Ask for code review before moving to next task

**For Senior Developers:**
- Review PRs from junior devs
- Handle complex integrations (WebSocket, PWA)
- Optimize performance bottlenecks
- Ensure architectural consistency

**For QA:**
- Use testing checklists in each phase
- Test on multiple browsers/devices
- Verify all user roles
- Check error handling

---

[← Back to Implementation Plan](README.md) | [← Phase 6](phase_6.md) | **COMPLETE** ✅
