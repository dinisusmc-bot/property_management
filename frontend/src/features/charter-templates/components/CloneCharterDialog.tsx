import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Typography,
  Alert,
} from '@mui/material'
import { useCloneCharter } from '../hooks/useTemplates'
import { format, addDays } from 'date-fns'

interface CloneCharterDialogProps {
  open: boolean
  onClose: () => void
  charterId: number
  currentTripDate: string
}

export function CloneCharterDialog({
  open,
  onClose,
  charterId,
  currentTripDate,
}: CloneCharterDialogProps) {
  const [newTripDate, setNewTripDate] = useState(
    format(addDays(new Date(currentTripDate), 7), 'yyyy-MM-dd')
  )

  const cloneMutation = useCloneCharter()

  const handleSubmit = () => {
    cloneMutation.mutate(
      {
        charter_id: charterId,
        trip_date: newTripDate,
      },
      {
        onSuccess: () => {
          onClose()
        },
      }
    )
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Clone Charter</DialogTitle>
      <DialogContent>
        <Box mt={2}>
          <Alert severity="info" sx={{ mb: 3 }}>
            This will create a duplicate charter with the same details but a different date.
          </Alert>

          <TextField
            fullWidth
            type="date"
            label="New Trip Date"
            value={newTripDate}
            onChange={(e) => setNewTripDate(e.target.value)}
            InputLabelProps={{ shrink: true }}
            sx={{ mb: 2 }}
          />

          <Typography variant="caption" color="text.secondary" display="block" mt={1}>
            Current trip date: {format(new Date(currentTripDate), 'MMM dd, yyyy')}
          </Typography>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={cloneMutation.isPending}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!newTripDate || cloneMutation.isPending}
        >
          {cloneMutation.isPending ? 'Cloning...' : 'Clone Charter'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
