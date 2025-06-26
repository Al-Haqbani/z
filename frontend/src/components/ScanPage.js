import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Typography, Button, Table, TableHead, TableRow,
  TableCell, TableBody, Stack
} from '@mui/material';

export default function ScanPage() {
  const { scanId } = useParams();
  const [results, setResults] = useState([]);
  const [progress, setProgress] = useState('');
  const [status, setStatus] = useState('running');

  useEffect(() => {
    const evt = new EventSource(`/stream/${scanId}`);
    evt.onmessage = e => {
      const data = JSON.parse(e.data);
      setResults(prev => [...prev, data]);
    };
    evt.addEventListener('progress', e => {
      const info = JSON.parse(e.data);
      setProgress(`${info.repo || ''} ${info.status || ''}`);
    });
    evt.addEventListener('done', () => {
      setStatus('done');
      evt.close();
    });
    return () => evt.close();
  }, [scanId]);

  const sendAction = action => {
    fetch(`/api/scan/${scanId}/${action}`, { method: 'POST' });
  };

  return (
    <div>
      <Typography variant="h5" gutterBottom>Scan {scanId}</Typography>
      <Typography variant="subtitle1" gutterBottom>{progress}</Typography>
      <Stack direction="row" spacing={2} sx={{ mb:2 }}>
        <Button variant="contained" onClick={() => sendAction('pause')}>Pause</Button>
        <Button variant="contained" onClick={() => sendAction('resume')}>Resume</Button>
        <Button variant="contained" color="error" onClick={() => sendAction('cancel')}>Cancel</Button>
        {status === 'done' && (
          <Button variant="contained" href={`/download/${scanId}.html`}>Download Report</Button>
        )}
      </Stack>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>#</TableCell>
            <TableCell>Source</TableCell>
            <TableCell>File</TableCell>
            <TableCell>Leak Type</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {results.map((r, idx) => (
            <TableRow key={idx}>
              <TableCell>{idx+1}</TableCell>
              <TableCell>{r.source}</TableCell>
              <TableCell><a href={r.file} target="_blank" rel="noreferrer">{r.file}</a></TableCell>
              <TableCell>{r.leak_type}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
