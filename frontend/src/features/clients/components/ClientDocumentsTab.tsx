/**
 * Client Documents Tab Component
 */
import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Typography,
  Paper,
  Button
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import { format } from 'date-fns'
import { Download as DownloadIcon } from '@mui/icons-material'

interface ClientDocumentsTabProps {
  clientId: number
}

export default function ClientDocumentsTab({ clientId }: ClientDocumentsTabProps) {
  const { data: documents, isLoading } = useQuery({
    queryKey: ['client-documents', clientId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/documents?client_id=${clientId}`)
      return response.data
    }
  })
  
  const getDocumentTypeColor = (type: string) => {
    const colors: Record<string, any> = {
      coi: 'primary',
      contract: 'secondary',
      id: 'info',
      insurance: 'success',
      other: 'default'
    }
    return colors[type] || 'default'
  }

  if (isLoading) {
    return <Typography>Loading...</Typography>
  }

  return (
    <Box>
      {/* Summary */}
      <Box mb={2} p={2} sx={{ bgcolor: 'background.default', borderRadius: 1 }}>
        <Typography variant="h6">
          Documents ({documents?.length || 0})
        </Typography>
      </Box>
      
      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Document Name</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Date Uploaded</TableCell>
              <TableCell>Expires</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="center">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {documents?.map((doc: any) => (
              <TableRow key={doc.id} hover>
                <TableCell>{doc.filename || 'Untitled'}</TableCell>
                <TableCell>
                  <Chip
                    label={doc.document_type || 'unknown'}
                    color={getDocumentTypeColor(doc.document_type || '')}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {doc.created_at ? format(new Date(doc.created_at), 'MMM dd, yyyy') : '-'}
                </TableCell>
                <TableCell>
                  {doc.expiration_date 
                    ? format(new Date(doc.expiration_date), 'MMM dd, yyyy')
                    : 'Never'}
                </TableCell>
                <TableCell>
                  <Chip
                    label={doc.status || 'active'}
                    color={doc.status === 'expired' ? 'error' : 'success'}
                    size="small"
                  />
                </TableCell>
                <TableCell align="center">
                  {doc.file_url && (
                    <Button
                      size="small"
                      startIcon={<DownloadIcon />}
                      onClick={() => window.open(doc.file_url, '_blank')}
                    >
                      Download
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {documents?.length === 0 && !isLoading && (
        <Box textAlign="center" py={4}>
          <Typography color="text.secondary">
            No documents found for this client
          </Typography>
        </Box>
      )}
    </Box>
  )
}
