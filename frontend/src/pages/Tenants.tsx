import React from 'react';
import { Box, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, IconButton, Chip } from '@mui/material';
import { glass } from '../theme';
import { DashboardLayout } from '../components/DashboardLayout';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import EditIcon from '@mui/icons-material/Edit';

const Tenants: React.FC = () => {
  return (
    <DashboardLayout>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h2" fontWeight={700}>Tenants</Typography>
          <Button variant="contained" startIcon={<AddIcon />} sx={{ borderRadius: 2 }}>Add Tenant</Button>
        </Box>
        <TextField
          variant="outlined"
          placeholder="Search tenants..."
          InputProps={{ startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />, sx: { ...glass, borderRadius: 2 } }}
          sx={{ width: 300 }}
        />
      </Box>

      <TableContainer component={Paper} sx={{ ...glass, borderRadius: 2 }}>
        <Table>
          <TableHead>
            <TableRow sx={{ '& .MuiTableCell-head': { fontWeight: 600, color: 'text.secondary' } }}>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Unit</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Co-Tenants</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}>
              <TableCell sx={{ fontWeight: 500 }}>Jane Doe</TableCell>
              <TableCell>jane.doe@example.com</TableCell>
              <TableCell>101 - Studio</TableCell>
              <TableCell>(555) 987-6543</TableCell>
              <TableCell><Chip label="2" size="small" sx={{ bgcolor: 'rgba(99,102,241,0.15)', color: '#6366f1' }} /></TableCell>
              <TableCell><Box sx={{ px: 1, py: 0.5, bgcolor: '#10b9811a', color: '#10b981', borderRadius: 1 }}>Active</Box></TableCell>
              <TableCell><IconButton size="small"><EditIcon /></IconButton></TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </DashboardLayout>
  );
};

export default Tenants;
