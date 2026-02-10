import React, { useState } from 'react';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer,
  TableHead, TableRow, Paper, TextField, IconButton, Modal, TextField as MUITextField, Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import { glass } from '../theme';
import { DashboardLayout } from '../components/DashboardLayout';
import AddIcon from '@mui/icons-material/Add';
import SearchIcon from '@mui/icons-material/Search';
import EditIcon from '@mui/icons-material/Edit';
import { useOwners } from '../hooks/useOwners';

const Properties: React.FC = () => {
  const [open, setOpen] = useState(false);
  const { data: owners = [] } = useOwners();

  return (
    <DashboardLayout>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h2" fontWeight={700}>Properties</Typography>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setOpen(true)} sx={{ borderRadius: 2 }}>
            Add Property
          </Button>
        </Box>
        <TextField
          variant="outlined"
          placeholder="Search properties..."
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
              <TableCell>Address</TableCell>
              <TableCell>Owner</TableCell>
              <TableCell>Units</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            <TableRow hover sx={{ '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' } }}>
              <TableCell sx={{ fontWeight: 500 }}>Sunset Ridge Apartments</TableCell>
              <TableCell>1234 Sunset Blvd, Los Angeles, CA</TableCell>
              <TableCell>John Smith</TableCell>
              <TableCell>24</TableCell>
              <TableCell><Box sx={{ px: 1, py: 0.5, bgcolor: '#10b9811a', color: '#10b981', borderRadius: 1 }}>Active</Box></TableCell>
              <TableCell><IconButton size="small"><EditIcon /></IconButton></TableCell>
            </TableRow>
          </TableBody>
        </Table>
      </TableContainer>

      <Modal open={open} onClose={() => setOpen(false)}>
        <Box sx={{
          position: 'absolute' as 'absolute',
          top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          width: 400,
          bgcolor: 'background.paper',
          boxShadow: 24,
          p: 4,
          ...glass,
        }}>
          <Typography variant="h6" fontWeight={700} mb={3}>Add Property</Typography>
          <Box component="form" sx={{ '& .MuiTextField-root': { mb: 2 } }}>
            <MUITextField fullWidth label="Name" variant="outlined" />
            <MUITextField fullWidth label="Address" variant="outlined" />
            <FormControl fullWidth>
              <InputLabel>Owner</InputLabel>
              <Select defaultValue="" label="Owner">
                {owners.map(o => <MenuItem key={o.id} value={o.id}>{o.full_name}</MenuItem>)}
              </Select>
            </FormControl>
            <Button fullWidth variant="contained" sx={{ mt: 2, borderRadius: 2 }}>Create</Button>
          </Box>
        </Box>
      </Modal>
    </DashboardLayout>
  );
};

export default Properties;
