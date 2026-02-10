import React from 'react';
import {
  Box,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  IconButton,
} from '@mui/material';
import { glass } from '../theme';
import { DashboardLayout } from '../components/DashboardLayout';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';

const Owners: React.FC = () => {
  return (
    <DashboardLayout>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h2" fontWeight={700}>Owners</Typography>
          <Button variant="contained" startIcon={<AddIcon />} sx={{ borderRadius: 2 }}>
            Add Owner
          </Button>
        </Box>
        <TextField
          variant="outlined"
          placeholder="Search owners..."
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
            sx: { ...glass, borderRadius: 2 },
          }}
          sx={{ width: 300 }}
        />
      </Box>

      <TableContainer component={Paper} sx={{ ...glass, borderRadius: 2 }}>
        <Table>
          <TableHead>
            <TableRow sx={{ '& .MuiTableCell-head': { fontWeight: 600, color: 'text.secondary' } }}>
              <TableCell>Name</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Phone</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}>
              <TableCell sx={{ fontWeight: 500 }}>John Smith</TableCell>
              <TableCell>john.smith@example.com</TableCell>
              <TableCell>(555) 123-4567</TableCell>
              <TableCell>
                <Box sx={{ px: 1, py: 0.5, bgcolor: '#10b9811a', color: '#10b981', borderRadius: 1, width: 'fit-content' }}>
                  Active
                </Box>
              </TableCell>
              <TableCell>
                <IconButton size="small">Edit</IconButton>
              </TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>
    </DashboardLayout>
  );
};

export default Owners;
