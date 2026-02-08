import { useState } from 'react'
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  DirectionsBus as CharterIcon,
  People as ClientIcon,
  LocalShipping as VendorIcon,
  Person as UserIcon,
  Logout as LogoutIcon,
  Payments as PaymentsIcon,
  Contacts as LeadsIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

const drawerWidth = 240

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const { user, logout } = useAuthStore()
  const [mobileOpen, setMobileOpen] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleProfileMenuClose = () => {
    setAnchorEl(null)
  }

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // Hide navigation for vendors and drivers - they only see their dashboard
  const isVendor = user?.role === 'vendor'
  const isDriver = user?.role === 'driver'
  const hideNavigation = isVendor || isDriver

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard', showForVendor: false },
    { text: 'Leads', icon: <LeadsIcon />, path: '/leads', showForVendor: false },
    { text: 'Charters', icon: <CharterIcon />, path: '/charters', showForVendor: false },
    { text: 'Clients', icon: <ClientIcon />, path: '/clients', showForVendor: false },
    { text: 'Vendors', icon: <VendorIcon />, path: '/vendors', showForVendor: false },
    { text: 'Accounts Receivable', icon: <PaymentsIcon />, path: '/receivables', showForVendor: false },
    { text: 'Accounts Payable', icon: <PaymentsIcon />, path: '/payables', showForVendor: false },
    { text: 'Payments', icon: <PaymentsIcon />, path: '/payments', showForVendor: false },
    { text: 'Users', icon: <UserIcon />, path: '/users', showForVendor: false },
  ]

  // Filter menu items based on user role
  const visibleMenuItems = hideNavigation 
    ? menuItems.filter(item => item.showForVendor)
    : menuItems

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap>
          Athena
        </Typography>
      </Toolbar>
      <Divider />
      {!hideNavigation && (
        <List>
          {visibleMenuItems.map((item) => (
            <ListItem key={item.text} disablePadding>
              <ListItemButton onClick={() => navigate(item.path)}>
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      )}
    </div>
  )

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: hideNavigation ? '100%' : { sm: `calc(100% - ${drawerWidth}px)` },
          ml: hideNavigation ? 0 : { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Charter Management
          </Typography>
          <IconButton onClick={handleProfileMenuOpen} sx={{ p: 0 }}>
            <Avatar>{user?.full_name.charAt(0) || 'U'}</Avatar>
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleProfileMenuClose}
          >
            <MenuItem disabled>
              <Typography variant="body2">{user?.email}</Typography>
            </MenuItem>
            <Divider />
            <MenuItem onClick={handleLogout}>
              <ListItemIcon>
                <LogoutIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Logout</ListItemText>
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>
      {!hideNavigation && (
        <Box
          component="nav"
          sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        >
          <Drawer
            variant="temporary"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{ keepMounted: true }}
            sx={{
              display: { xs: 'block', sm: 'none' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: drawerWidth,
              },
            }}
          >
            {drawer}
          </Drawer>
          <Drawer
            variant="permanent"
            sx={{
              display: { xs: 'none', sm: 'block' },
              '& .MuiDrawer-paper': {
                boxSizing: 'border-box',
                width: drawerWidth,
              },
            }}
            open
          >
            {drawer}
          </Drawer>
        </Box>
      )}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: hideNavigation ? '100%' : { sm: `calc(100% - ${drawerWidth}px)` },
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  )
}
