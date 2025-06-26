import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ScanPage from './components/ScanPage';
import { AppBar, Toolbar, Typography, Container } from '@mui/material';

export default function App() {
  return (
    <div>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            EmploLeaksGuardian
          </Typography>
          <Link to="/" style={{ color: 'inherit', textDecoration: 'none' }}>Dashboard</Link>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scan/:scanId" element={<ScanPage />} />
        </Routes>
      </Container>
    </div>
  );
}
