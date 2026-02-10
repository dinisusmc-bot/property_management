import React from 'react';
import { Box, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, TextField, IconButton, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { glass } from '../theme';
import { DashboardLayout } from '../components/DashboardLayout';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import EditIcon from '@mui/icons-material/Edit';

const Units: React.FC = () => {
  return (
    <DashboardLayout>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h2" fontWeight={700}>Units</Typography>
          <Button variant="contained" startIcon={<AddIcon />} sx={{ borderRadius: 2 }}>Add Unit</Button>
        </Box>
        <TextField
          variant="outlined"
          placeholder="Search units..."
          InputProps={{ startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />, sx: { ...glass, borderRadius: 2 } }}
          sx={{ width: 300 }}
        />
      </Box>

      <TableContainer component={Paper} sx={{ ...glass, borderRadius: 2 }}>
        <Table>
          <TableHead>
            <TableRow sx={{ '& .MuiTableCell-head': { fontWeight: 600, color: 'text.secondary' } }}>
              <TableCell>Unit #</TableCell>
              <TableCell>Property</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Rent</TableCell>
              <TableCell>Tenant</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}>
              <TableCell sx={{ fontWeight: 500 }}>101</TableCell>
              <TableCell>Sunset Ridge Apartments</TableCell>
              <TableCell>Studio</TableCell>
              <TableCell>$1,800/mo</TableCell>
              <TableCell>Jane Doe</TableCell>
              <TableCell><Box sx={{ px: 1, py: 0.5, bgcolor: '#10b9811a', color: '#10b981', borderRadius: 1 }}>Occupied</Box></TableCell>
              <TableCell><IconButton size="small"><EditIcon /></IconButton></TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </DashboardLayout>
  );
};

export default Units;
