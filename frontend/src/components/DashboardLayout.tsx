import React from 'react';
import { Box, Drawer, AppBar, Toolbar, List, Typography, Divider, ListItem, ListItemIcon, ListItemText, CssBaseline } from '@mui/material';
import { glass } from '../theme';
import DashboardIcon from '@mui/icons-material/Dashboard';
import PeopleIcon from '@mui/icons-material/People';
import HomeWorkIcon from '@mui/icons-material/HomeWork';
import BusinessIcon from '@mui/icons-material/Business';
import BuildIcon from '@mui/icons-material/Build';
import DescriptionIcon from '@mui/icons-material/Description';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';

const drawerWidth = 260;

export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          ...glass,
          zIndex: (theme) => theme.zIndex.drawer + 1,
          borderBottom: '1px solid rgba(255,255,255,0.08)',
        }}
      >
        <Toolbar>
          <Typography variant="h6" noWrap component="div" fontWeight={700}>
            Property Manager
          </Typography>
        </Toolbar>
      </AppBar>
      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
            ...glass,
            borderRight: '1px solid rgba(255,255,255,0.05)',
          },
        }}
      >
        <Toolbar />
        <List>
          {[
            { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
            { text: 'Owners', icon: <PeopleIcon />, path: '/owners' },
            { text: 'Properties', icon: <BusinessIcon />, path: '/properties' },
            { text: 'Units', icon: <HomeWorkIcon />, path: '/units' },
            { text: 'Maintenance', icon: <BuildIcon />, path: '/maintenance' },
            { text: 'Leases', icon: <DocumentIcon />, path: '/leases' },
          ].map((item) => (
            <ListItem button key={item.text} component="a" href={item.path}>
              <ListItemIcon sx={{ color: 'text.secondary' }}>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} sx={{ fontWeight: 500 }} />
            </ListItem>
          ))}
        </List>
        <Divider />
        <List>
          <ListItem button component="a" href="/settings">
            <ListItemIcon sx={{ color: 'text.secondary' }}><SettingsIcon /></ListItemIcon>
            <ListItemText primary="Settings" sx={{ fontWeight: 500 }} />
          </ListItem>
          <ListItem button component="a" href="/logout">
            <ListItemIcon sx={{ color: 'text.secondary' }}><LogoutIcon /></ListItemIcon>
            <ListItemText primary="Logout" sx={{ fontWeight: 500 }} />
          </ListItem>
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        {children}
      </Box>
    </Box>
  );
};
