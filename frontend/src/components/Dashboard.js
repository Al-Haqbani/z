import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, Typography, Grid, Card, CardContent } from '@mui/material';

export default function Dashboard() {
  const [scans, setScans] = useState([]);
  useEffect(() => { fetch('/api/scans').then(res => res.json()).then(setScans); }, []);

  const metrics = { total: scans ? Object.keys(scans).length : 0 };
  return (
    <div>
      <Typography variant="h4" gutterBottom>Scan History</Typography>
      <Grid container spacing={2} sx={{ mb:2 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: '#1f1b2d', color: 'white' }}><CardContent><Typography variant="h5">Scans</Typography><Typography>{metrics.total}</Typography></CardContent></Card>
        </Grid>
      </Grid>
      <TableContainer component={Paper} sx={{ bgcolor: '#1e1e1e' }}>
        <Table size="small" sx={{ color: 'white' }}>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Keyword</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Leaks</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(scans).map(([id, s]) => (
              <TableRow key={id}>
                <TableCell>{id}</TableCell>
                <TableCell>{s.keyword}</TableCell>
                <TableCell>{s.status}</TableCell>
                <TableCell>{s.results.length}</TableCell>
                <TableCell>
                  <Button component={Link} to={`/scan/${id}`} size="small" variant="contained">View</Button>
                  {s.status === 'done' && (
                    <Button href={`/download/${id}.html`} size="small" sx={{ ml:1 }} variant="outlined">Report</Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
