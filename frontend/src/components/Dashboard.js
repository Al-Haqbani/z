import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, Button, Typography, Grid, Card, CardContent, Chip } from '@mui/material';
import { BarChart } from '@tremor/react';
import { FadeIn } from 'reactbits';

export default function Dashboard() {
  const [scans, setScans] = useState([]);
  useEffect(() => { fetch('/api/scans').then(res => res.json()).then(setScans); }, []);

  const metrics = {
    total: scans ? Object.keys(scans).length : 0,
    running: scans ? Object.values(scans).filter(s => s.status==='running').length : 0,
    leaks: scans ? Object.values(scans).reduce((a,b)=>a+b.results.length,0) : 0,
  };
  const severityCounts = { high:0, medium:0, low:0, info:0 };
  Object.values(scans).forEach(s => {
    (s.results || []).forEach(r => {
      const sev = r.severity || 'info';
      if(severityCounts[sev] !== undefined) severityCounts[sev]++;
    });
  });
  const chartData = [
    { type: 'High', count: severityCounts.high },
    { type: 'Medium', count: severityCounts.medium },
    { type: 'Low', count: severityCounts.low },
    { type: 'Info', count: severityCounts.info },
  ];
  return (
    <div>
      <Typography variant="h4" gutterBottom>Scan History</Typography>
      <Grid container spacing={2} sx={{ mb:2 }}>
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: '#1f1b2d', color: 'white' }}><CardContent><Typography variant="h6">Scans</Typography><Typography>{metrics.total}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: '#1f1b2d', color: 'white' }}><CardContent><Typography variant="h6">Running</Typography><Typography>{metrics.running}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: '#1f1b2d', color: 'white' }}><CardContent><Typography variant="h6">Leaks</Typography><Typography>{metrics.leaks}</Typography></CardContent></Card>
        </Grid>
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: '#1f1b2d', color: 'white' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>Severity Breakdown</Typography>
              <BarChart
                data={chartData}
                index="type"
                categories={["count"]}
                colors={["red","orange","yellow","blue"]}
                className="mt-2 h-40"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      <TableContainer component={Paper} sx={{ bgcolor: '#1e1e1e' }}>
        <Table size="small" sx={{ color: 'white' }}>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Keyword</TableCell>
              <TableCell>Started</TableCell>
              <TableCell>Finished</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Leaks</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {Object.entries(scans).map(([id, s]) => (
              <FadeIn key={id}>
                <TableRow>
                  <TableCell>{id}</TableCell>
                  <TableCell>{s.keyword}</TableCell>
                  <TableCell>{s.started}</TableCell>
                  <TableCell>{s.finished || '-'}</TableCell>
                  <TableCell>
                    <Chip label={s.status} color={s.status==='running' ? 'warning' : s.status==='failed'? 'error':'success'} size="small" />
                  </TableCell>
                  <TableCell>{s.results.length}</TableCell>
                  <TableCell>
                    <Button component={Link} to={`/scan/${id}`} size="small" variant="contained">View</Button>
                    {s.status === 'done' && (
                      <Button href={`/download/${id}.html`} size="small" sx={{ ml:1 }} variant="outlined">Report</Button>
                    )}
                  </TableCell>
                </TableRow>
              </FadeIn>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
