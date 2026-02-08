import { useState } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Box,
  Alert,
} from '@mui/material'
import { useCreateTemplate } from '../hooks/useTemplates'

interface SaveAsTemplateDialogProps {
  open: boolean
  onClose: () => void
  charterId: number
}

export function SaveAsTemplateDialog({ open, onClose, charterId }: SaveAsTemplateDialogProps) {
  const [name, setName] = useState('')

  const createTemplateMutation = useCreateTemplate()

  const handleSubmit = () => {
    createTemplateMutation.mutate(
      {
        charter_id: charterId,
        template_name: name,
      },
      {
        onSuccess: () => {
          setName('')
          onClose()
        },
      }
    )
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Save as Template</DialogTitle>
      <DialogContent>
        <Box mt={2}>
          <Alert severity="info" sx={{ mb: 3 }}>
            Save this charter configuration as a reusable template for future bookings
          </Alert>

          <TextField
            fullWidth
            label="Template Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Airport Transfer - Standard"
            sx={{ mb: 2 }}
            required
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={createTemplateMutation.isPending}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={!name.trim() || createTemplateMutation.isPending}
        >
          {createTemplateMutation.isPending ? 'Saving...' : 'Save Template'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
