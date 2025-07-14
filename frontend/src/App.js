import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ScanPage from './components/ScanPage';
import Tokens from './components/Tokens';
import Settings from './components/Settings';
import Layout from './components/Layout';
import { ThemeProvider, createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#7F3FBF' },
    background: { default: '#0e101c', paper: '#1e1e2f' },
    text: { primary: '#FFFFFF', secondary: '#B0B3B8' }
  },
  typography: {
    fontFamily: 'Inter, sans-serif',
    h5: { fontFamily: 'Poppins, sans-serif' },
  },
});

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scan/:scanId" element={<ScanPage />} />
          <Route path="/scans" element={<Dashboard />} />
          <Route path="/tokens" element={<Tokens />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </ThemeProvider>
  );
}
