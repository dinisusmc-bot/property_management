/**
 * Change Case List - Main management page for viewing and filtering change cases
 */
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Chip,
  IconButton,
  Button,
  TextField,
  MenuItem,
  Grid,
  CircularProgress,
  Alert
} from '@mui/material'
import {
  Visibility as ViewIcon,
  Add as AddIcon,
  FilterList as FilterIcon
} from '@mui/icons-material'
import { useChangeCases } from '../hooks/useChangeQuery'
import { ChangeStatus, ChangePriority, ChangeType, type ChangeCaseFilters } from '../types/change.types'

export default function ChangeCaseList() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<ChangeCaseFilters>({
    page: 1,
    page_size: 50
  })
  const [showFilters, setShowFilters] = useState(false)

  const { data, isLoading, error } = useChangeCases(filters)

  const getStatusColor = (status: ChangeStatus): 'default' | 'warning' | 'success' | 'error' | 'info' => {
    switch (status) {
      case ChangeStatus.PENDING:
        return 'warning'
      case ChangeStatus.UNDER_REVIEW:
        return 'info'
      case ChangeStatus.APPROVED:
        return 'success'
      case ChangeStatus.IMPLEMENTED:
        return 'success'
      case ChangeStatus.REJECTED:
        return 'error'
      case ChangeStatus.CANCELLED:
        return 'default'
      default:
        return 'default'
    }
  }

  const getPriorityColor = (priority: ChangePriority): 'default' | 'warning' | 'error' | 'info' => {
    switch (priority) {
      case ChangePriority.LOW:
        return 'info'
      case ChangePriority.MEDIUM:
        return 'default'
      case ChangePriority.HIGH:
        return 'warning'
      case ChangePriority.URGENT:
        return 'error'
      default:
        return 'default'
    }
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString()
  }

  const handleFilterChange = (field: keyof ChangeCaseFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [field]: value || undefined,
      page: 1 // Reset to first page when filters change
    }))
  }

  const clearFilters = () => {
    setFilters({ page: 1, page_size: 50 })
  }

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">
          Failed to load change cases: {error instanceof Error ? error.message : 'Unknown error'}
        </Alert>
      </Box>
    )
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Change Management</Typography>
        <Box>
          <Button
            startIcon={<FilterIcon />}
            onClick={() => setShowFilters(!showFilters)}
            sx={{ mr: 2 }}
          >
            {showFilters ? 'Hide' : 'Show'} Filters
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/changes/new')}
          >
            New Change Case
          </Button>
        </Box>
      </Box>

      {showFilters && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                label="Charter ID"
                type="number"
                value={filters.charter_id || ''}
                onChange={(e) => handleFilterChange('charter_id', e.target.value ? Number(e.target.value) : undefined)}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                select
                label="Status"
                value={filters.status || ''}
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                {Object.values(ChangeStatus).map((status) => (
                  <MenuItem key={status} value={status}>
                    {status.replace(/_/g, ' ').toUpperCase()}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                select
                label="Priority"
                value={filters.priority || ''}
                onChange={(e) => handleFilterChange('priority', e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                {Object.values(ChangePriority).map((priority) => (
                  <MenuItem key={priority} value={priority}>
                    {priority.toUpperCase()}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                fullWidth
                select
                label="Change Type"
                value={filters.change_type || ''}
                onChange={(e) => handleFilterChange('change_type', e.target.value)}
              >
                <MenuItem value="">All</MenuItem>
                {Object.values(ChangeType).map((type) => (
                  <MenuItem key={type} value={type}>
                    {type.replace(/_/g, ' ').toUpperCase()}
                  </MenuItem>
                ))}
              </TextField>
            </Grid>
            <Grid item xs={12}>
              <Button onClick={clearFilters}>Clear Filters</Button>
            </Grid>
          </Grid>
        </Paper>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Case #</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Charter ID</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell>Requested By</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.items && data.items.length > 0 ? (
              data.items.map((changeCase) => (
                <TableRow key={changeCase.id} hover>
                  <TableCell>{changeCase.case_number}</TableCell>
                  <TableCell>{changeCase.title}</TableCell>
                  <TableCell>{changeCase.charter_id}</TableCell>
                  <TableCell>
                    {changeCase.change_type.replace(/_/g, ' ')}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={changeCase.status.replace(/_/g, ' ')}
                      color={getStatusColor(changeCase.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={changeCase.priority}
                      color={getPriorityColor(changeCase.priority)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{changeCase.requested_by_name}</TableCell>
                  <TableCell>{formatDate(changeCase.created_at)}</TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/changes/${changeCase.id}`)}
                      title="View Details"
                    >
                      <ViewIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body1" color="text.secondary" py={4}>
                    No change cases found
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {data && data.total > 0 && (
        <Box mt={2} display="flex" justifyContent="space-between" alignItems="center">
          <Typography variant="body2" color="text.secondary">
            Showing {data.items.length} of {data.total} change cases
          </Typography>
          <Box>
            <Button
              disabled={data.page === 1}
              onClick={() => handleFilterChange('page', (filters.page || 1) - 1)}
            >
              Previous
            </Button>
            <Typography variant="body2" component="span" mx={2}>
              Page {data.page} of {data.total_pages}
            </Typography>
            <Button
              disabled={data.page >= data.total_pages}
              onClick={() => handleFilterChange('page', (filters.page || 1) + 1)}
            >
              Next
            </Button>
          </Box>
        </Box>
      )}
    </Box>
  )
}
