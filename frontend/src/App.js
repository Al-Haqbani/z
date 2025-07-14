import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import ScanPage from './components/ScanPage';
import Layout from './components/Layout';
import { ThemeProvider, createTheme } from '@mui/material/styles';

const theme = createTheme({ palette: { mode: 'dark', primary: { main: '#7F3FBF' } } });

export default function App() {
  return (
    <ThemeProvider theme={theme}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scan/:scanId" element={<ScanPage />} />
          <Route path="/scans" element={<Dashboard />} />
        </Routes>
      </Layout>
    </ThemeProvider>
  );
}
