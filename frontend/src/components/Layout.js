import React from 'react';
import { Link } from 'react-router-dom';
import { Box, Drawer, List, ListItem, ListItemIcon, ListItemText, AppBar, Toolbar, Typography, IconButton } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import HistoryIcon from '@mui/icons-material/History';
import RadarIcon from '@mui/icons-material/Radar';
import SettingsIcon from '@mui/icons-material/Settings';
import VpnKeyIcon from '@mui/icons-material/VpnKey';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

export default function Layout({ children }) {
  const drawerWidth = 200;
  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: 1201 }}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            EmploLeaksGuardian
          </Typography>
          <IconButton color="inherit" component={Link} to="/">
            <PlayArrowIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer variant="permanent" sx={{ width: drawerWidth, [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box', backgroundColor: '#0e101c', color: 'white' } }}>
        <Toolbar />
        <List>
          <ListItem button component={Link} to="/">
            <ListItemIcon sx={{ color: 'inherit' }}><DashboardIcon /></ListItemIcon>
            <ListItemText primary="Dashboard" />
          </ListItem>
          <ListItem button component={Link} to="/scans">
            <ListItemIcon sx={{ color: 'inherit' }}><HistoryIcon /></ListItemIcon>
            <ListItemText primary="Scan History" />
          </ListItem>
          <ListItem button component={Link} to="/scan/active">
            <ListItemIcon sx={{ color: 'inherit' }}><RadarIcon /></ListItemIcon>
            <ListItemText primary="Live Scan" />
          </ListItem>
          <ListItem button component={Link} to="/tokens">
            <ListItemIcon sx={{ color: 'inherit' }}><VpnKeyIcon /></ListItemIcon>
            <ListItemText primary="Tokens Vault" />
          </ListItem>
          <ListItem button component={Link} to="/settings">
            <ListItemIcon sx={{ color: 'inherit' }}><SettingsIcon /></ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItem>
        </List>
      </Drawer>
      <Box component="main" sx={{ flexGrow: 1, p: 3, bgcolor: '#121212', minHeight: '100vh' }}>
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}
