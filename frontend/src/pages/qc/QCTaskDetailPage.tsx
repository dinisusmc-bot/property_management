/**
 * QC Task Detail Page
 */
import { useParams } from 'react-router-dom'
import { Box, CircularProgress, Alert, Paper, Typography } from '@mui/material'
import { useQCTask } from '../../features/qc/hooks/useQcQuery'

export default function QCTaskDetailPage() {
  const { id } = useParams<{ id: string }>()
  const taskId = id ? parseInt(id, 10) : null

  const { data, isLoading, error } = useQCTask(taskId!)

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  if (error || !data) {
    return <Alert severity="error">Failed to load QC task</Alert>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        QC Task #{data.id}
      </Typography>
      
      <Paper sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Details
        </Typography>
        <Box sx={{ mt: 2 }}>
          <Typography><strong>Charter:</strong> {data.charter_reference || `#${data.charter_id}`}</Typography>
          <Typography><strong>Type:</strong> {data.task_type}</Typography>
          <Typography><strong>Status:</strong> {data.status}</Typography>
          <Typography><strong>Due Date:</strong> {new Date(data.due_date).toLocaleDateString()}</Typography>
          <Typography><strong>Assigned To:</strong> {data.assigned_to_name || 'Unassigned'}</Typography>
          {data.completed_at && (
            <Typography><strong>Completed:</strong> {new Date(data.completed_at).toLocaleDateString()}</Typography>
          )}
          {data.notes && (
            <Typography><strong>Notes:</strong> {data.notes}</Typography>
          )}
        </Box>
      </Paper>
    </Box>
  )
}
