import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Chip,
  IconButton,
  TextField,
  MenuItem,
  Grid,
  Typography,
  CircularProgress
} from '@mui/material'
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as ViewIcon,
  CheckCircle as ConvertIcon
} from '@mui/icons-material'
import { useLeads, useDeleteLead, useConvertLead } from '../hooks/useLeads'
import { Lead, LeadFilters } from '../types/lead.types'
import { format } from 'date-fns'

export default function LeadList() {
  const navigate = useNavigate()
  const [page, setPage] = useState(0)
  const [rowsPerPage, setRowsPerPage] = useState(25)
  const [filters, setFilters] = useState<LeadFilters>({})
  
  const { data: leads, isLoading } = useLeads()
  const deleteMutation = useDeleteLead()
  const convertMutation = useConvertLead()
  
  const getStatusColor = (status: string): any => {
    const colors = {
      new: 'info',
      contacted: 'primary',
      qualified: 'secondary',
      negotiating: 'warning',
      converted: 'success',
      dead: 'error'
    }
    return colors[status as keyof typeof colors] || 'default'
  }
  
  const handleDelete = (id: number, name: string) => {
    if (confirm(`Are you sure you want to delete lead "${name}"?`)) {
      deleteMutation.mutate(id)
    }
  }
  
  const handleConvert = (id: number, name: string) => {
    if (confirm(`Convert lead "${name}" to quote?`)) {
      convertMutation.mutate(id, {
        onSuccess: (data) => {
          navigate(`/charters/${data.charter_id}`)
        }
      })
    }
  }
  
  const normalizedSearch = (filters.search || '').toLowerCase().trim()
  const filteredLeads = (leads || []).filter((lead) => {
    const matchesStatus = !filters.status || lead.status === filters.status
    const matchesSource = !filters.source || lead.source === filters.source

    const matchesSearch = !normalizedSearch || [
      lead.first_name,
      lead.last_name,
      lead.email,
      lead.phone || '',
      lead.company_name || '',
    ].some((value) => value.toLowerCase().includes(normalizedSearch))

    const createdAt = new Date(lead.created_at)
    const matchesFromDate = !filters.date_from || createdAt >= new Date(filters.date_from)
    const matchesToDate = !filters.date_to || createdAt <= new Date(filters.date_to)

    return matchesStatus && matchesSource && matchesSearch && matchesFromDate && matchesToDate
  })

  const paginatedLeads = filteredLeads.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
  
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }
  
  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Leads</Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/leads/new')}
        >
          New Lead
        </Button>
      </Box>
      
      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              size="small"
              label="Search"
              placeholder="Name, email, phone..."
              value={filters.search || ''}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              select
              size="small"
              label="Status"
              value={filters.status || ''}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            >
              <MenuItem value="">All Statuses</MenuItem>
              <MenuItem value="new">New</MenuItem>
              <MenuItem value="contacted">Contacted</MenuItem>
              <MenuItem value="qualified">Qualified</MenuItem>
              <MenuItem value="negotiating">Negotiating</MenuItem>
              <MenuItem value="converted">Converted</MenuItem>
              <MenuItem value="dead">Dead</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              select
              size="small"
              label="Source"
              value={filters.source || ''}
              onChange={(e) => setFilters({ ...filters, source: e.target.value })}
            >
              <MenuItem value="">All Sources</MenuItem>
              <MenuItem value="web">Web</MenuItem>
              <MenuItem value="phone">Phone</MenuItem>
              <MenuItem value="email">Email</MenuItem>
              <MenuItem value="referral">Referral</MenuItem>
              <MenuItem value="walk_in">Walk In</MenuItem>
              <MenuItem value="partner">Partner</MenuItem>
            </TextField>
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              type="date"
              size="small"
              label="From Date"
              value={filters.date_from || ''}
              onChange={(e) => setFilters({ ...filters, date_from: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <TextField
              fullWidth
              type="date"
              size="small"
              label="To Date"
              value={filters.date_to || ''}
              onChange={(e) => setFilters({ ...filters, date_to: e.target.value })}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          <Grid item xs={12} md={1}>
            <Button
              fullWidth
              variant="outlined"
              onClick={() => setFilters({})}
              sx={{ height: '40px' }}
            >
              Clear
            </Button>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Data Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Company</TableCell>
              <TableCell>Contact</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Trip Date</TableCell>
              <TableCell>Assigned To</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedLeads && paginatedLeads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography color="textSecondary" py={4}>
                    No leads found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              paginatedLeads?.map((lead: Lead) => (
                <TableRow key={lead.id} hover>
                  <TableCell>{`${lead.first_name} ${lead.last_name}`}</TableCell>
                  <TableCell>{lead.company_name || '-'}</TableCell>
                  <TableCell>
                    <Typography variant="body2">{lead.email}</Typography>
                    <Typography variant="caption" color="textSecondary">
                      {lead.phone || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Chip label={lead.source} size="small" />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={lead.status}
                      color={getStatusColor(lead.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    {lead.estimated_trip_date ? format(new Date(lead.estimated_trip_date), 'MMM dd, yyyy') : '-'}
                  </TableCell>
                  <TableCell>{lead.assigned_agent_id ? `Agent ${lead.assigned_agent_id}` : 'Unassigned'}</TableCell>
                  <TableCell>
                    {format(new Date(lead.created_at), 'MMM dd, yyyy')}
                  </TableCell>
                  <TableCell align="center">
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/leads/${lead.id}`)}
                      title="View Details"
                    >
                      <ViewIcon />
                    </IconButton>
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/leads/${lead.id}/edit`)}
                      title="Edit"
                    >
                      <EditIcon />
                    </IconButton>
                    {lead.status !== 'converted' && (
                      <IconButton
                        size="small"
                        color="success"
                        onClick={() => handleConvert(lead.id, `${lead.first_name} ${lead.last_name}`)}
                        title="Convert to Quote"
                      >
                        <ConvertIcon />
                      </IconButton>
                    )}
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => handleDelete(lead.id, `${lead.first_name} ${lead.last_name}`)}
                      title="Delete"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={filteredLeads.length}
          page={page}
          onPageChange={(_, newPage) => setPage(newPage)}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={(e) => {
            setRowsPerPage(parseInt(e.target.value, 10))
            setPage(0)
          }}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </TableContainer>
    </Box>
  )
}
