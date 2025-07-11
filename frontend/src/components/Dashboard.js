import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, Button, Typography
} from '@mui/material';

export default function Dashboard() {
  const [scans, setScans] = useState([]);

  useEffect(() => {
    fetch('/api/scans').then(res => res.json()).then(setScans);
  }, []);

  return (
    <div>
      <Typography variant="h4" gutterBottom>Scan History</Typography>
      <TableContainer component={Paper}>
        <Table size="small">
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
                  <Button component={Link} to={`/scan/${id}`} size="small">View</Button>
                  {s.status === 'done' && (
                    <Button href={`/download/${id}.html`} size="small">Report</Button>
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
