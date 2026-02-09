/**
 * QC Task List Component
 * Main dashboard for viewing and managing QC tasks
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
  Chip,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  CircularProgress,
  Alert,
  Button,
  Stack
} from '@mui/material'
import { useQCTasks } from '../hooks/useQcQuery'
import { QCTaskStatus, QCTaskType, type QCTaskFilters } from '../types/qc.types'
import { format, isPast } from 'date-fns'
import { FilterList as FilterIcon, Add as AddIcon } from '@mui/icons-material'
import type { QCTask } from '../types/qc.types'

export default function QCTaskList() {
  const navigate = useNavigate()
  const [filters, setFilters] = useState<QCTaskFilters>({})
  
  const { data, isLoading, error } = useQCTasks(filters)

  const getStatusColor = (status: QCTaskStatus): 'default' | 'warning' | 'success' | 'error' | 'info' => {
    switch (status) {
      case QCTaskStatus.PENDING:
        return 'warning'
      case QCTaskStatus.IN_PROGRESS:
        return 'info'
      case QCTaskStatus.COMPLETED:
        return 'success'
      case QCTaskStatus.FAILED:
        return 'error'
      default:
        return 'default'
    }
  }
  
  const getTaskTypeLabel = (type: QCTaskType) => {
    const labels: Record<string, string> = {
      [QCTaskType.COI_VERIFICATION]: 'COI Verification',
      [QCTaskType.PAYMENT_VERIFICATION]: 'Payment Verification',
      [QCTaskType.ITINERARY_REVIEW]: 'Itinerary Review',
      [QCTaskType.DOCUMENT_CHECK]: 'Document Check',
      [QCTaskType.OTHER]: 'Other'
    }
    return labels[type] || type
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
      <Alert severity="error">Failed to load QC tasks</Alert>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">QC Tasks</Typography>
        <Stack direction="row" spacing={1}>
          <Button
            variant="contained"
            startIcon={<FilterIcon />}
            onClick={() => console.log('Filter clicked')}
          >
            Filter
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => console.log('Create task clicked')}
          >
            Create Task
          </Button>
        </Stack>
      </Box>
      
      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={filters.status || ''}
                label="Status"
                onChange={(e) => setFilters({ ...filters, status: e.target.value as QCTaskStatus | undefined })}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value={QCTaskStatus.PENDING}>Pending</MenuItem>
                <MenuItem value={QCTaskStatus.IN_PROGRESS}>In Progress</MenuItem>
                <MenuItem value={QCTaskStatus.COMPLETED}>Completed</MenuItem>
                <MenuItem value={QCTaskStatus.FAILED}>Failed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <FormControl fullWidth size="small">
              <InputLabel>Task Type</InputLabel>
              <Select
                value={filters.task_type || ''}
                label="Task Type"
                onChange={(e) => setFilters({ ...filters, task_type: e.target.value as QCTaskType | undefined })}
              >
                <MenuItem value="">All</MenuItem>
                <MenuItem value={QCTaskType.COI_VERIFICATION}>COI Verification</MenuItem>
                <MenuItem value={QCTaskType.PAYMENT_VERIFICATION}>Payment Verification</MenuItem>
                <MenuItem value={QCTaskType.ITINERARY_REVIEW}>Itinerary Review</MenuItem>
                <MenuItem value={QCTaskType.DOCUMENT_CHECK}>Document Check</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Paper>
      
      {/* Task Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Charter</TableCell>
              <TableCell>Task Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Assigned To</TableCell>
              <TableCell>Due Date</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data?.map((task: QCTask) => {
              const isOverdue = isPast(new Date(task.due_date)) && task.status !== QCTaskStatus.COMPLETED
              return (
                <TableRow
                  key={task.id}
                  hover
                  sx={{ 
                    cursor: 'pointer',
                    backgroundColor: isOverdue ? 'error.light' : 'inherit'
                  }}
                  onClick={() => navigate(`/qc-tasks/${task.id}`)}
                >
                  <TableCell>{task.id}</TableCell>
                  <TableCell>
                    {task.charter_reference || `Charter #${task.charter_id}`}
                  </TableCell>
                  <TableCell>{getTaskTypeLabel(task.task_type)}</TableCell>
                  <TableCell>
                    <Chip
                      label={task.status}
                      color={getStatusColor(task.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{task.assigned_to_name || 'Unassigned'}</TableCell>
                  <TableCell>
                    {format(new Date(task.due_date), 'MMM dd, yyyy')}
                    {isOverdue && (
                      <Chip label="OVERDUE" color="error" size="small" sx={{ ml: 1 }} />
                    )}
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label="View"
                      color="primary"
                      size="small"
                      onClick={(e) => {
                        e.stopPropagation()
                        navigate(`/qc-tasks/${task.id}`)
                      }}
                      sx={{ cursor: 'pointer' }}
                    />
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </TableContainer>
      
      {data?.length === 0 && (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">No QC tasks found</Typography>
        </Paper>
      )}
    </Box>
  )
}
