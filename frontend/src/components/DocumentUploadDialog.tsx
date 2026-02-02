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
  Typography,
  LinearProgress
} from '@mui/material'
import { CloudUpload as UploadIcon } from '@mui/icons-material'
import api from '../services/api'

interface DocumentUploadDialogProps {
  open: boolean
  onClose: () => void
  onUploadComplete: () => void
  charterId: number
  documentType?: string
  title: string
  additionalFields?: React.ReactNode
}

export default function DocumentUploadDialog({
  open,
  onClose,
  onUploadComplete,
  charterId,
  documentType = 'other',
  title,
  additionalFields
}: DocumentUploadDialogProps) {
  const [file, setFile] = useState<File | null>(null)
  const [description, setDescription] = useState('')
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [uploadProgress, setUploadProgress] = useState(0)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile) {
      // Validate file size (10MB)
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB')
        setFile(null)
        return
      }

      // Validate file extension
      const allowedExtensions = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'txt', 'csv']
      const fileExtension = selectedFile.name.split('.').pop()?.toLowerCase()
      if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
        setError(`File type not allowed. Allowed types: ${allowedExtensions.join(', ')}`)
        setFile(null)
        return
      }

      setFile(selectedFile)
      setError('')
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file')
      return
    }

    try {
      setUploading(true)
      setError('')
      setUploadProgress(0)

      const formData = new FormData()
      formData.append('file', file)
      formData.append('charter_id', charterId.toString())
      formData.append('document_type', documentType)
      if (description) {
        formData.append('description', description)
      }

      await api.post('/api/v1/documents/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent: any) => {
          if (progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
            setUploadProgress(progress)
          }
        }
      })

      // Call parent's callback with document ID if needed
      if (onUploadComplete) {
        onUploadComplete()
      }

      // Reset and close
      setFile(null)
      setDescription('')
      setUploadProgress(0)
      onClose()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload document')
    } finally {
      setUploading(false)
    }
  }

  const handleClose = () => {
    if (!uploading) {
      setFile(null)
      setDescription('')
      setError('')
      setUploadProgress(0)
      onClose()
    }
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 3, mt: 1 }}>
          <input
            accept=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.bmp,.txt,.csv"
            style={{ display: 'none' }}
            id="file-upload"
            type="file"
            onChange={handleFileChange}
            disabled={uploading}
          />
          <label htmlFor="file-upload">
            <Button
              variant="outlined"
              component="span"
              startIcon={<UploadIcon />}
              fullWidth
              disabled={uploading}
            >
              {file ? file.name : 'Choose File'}
            </Button>
          </label>
          {file && (
            <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
              Size: {(file.size / 1024).toFixed(2)} KB
            </Typography>
          )}
        </Box>

        {additionalFields}

        <TextField
          fullWidth
          label="Description (Optional)"
          multiline
          rows={3}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          disabled={uploading}
          sx={{ mb: 2 }}
        />

        {uploading && (
          <Box sx={{ width: '100%', mb: 2 }}>
            <LinearProgress variant="determinate" value={uploadProgress} />
            <Typography variant="caption" color="textSecondary" align="center" sx={{ display: 'block', mt: 1 }}>
              Uploading... {uploadProgress}%
            </Typography>
          </Box>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} disabled={uploading}>
          Cancel
        </Button>
        <Button
          onClick={handleUpload}
          variant="contained"
          disabled={!file || uploading}
        >
          {uploading ? 'Uploading...' : 'Upload'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
