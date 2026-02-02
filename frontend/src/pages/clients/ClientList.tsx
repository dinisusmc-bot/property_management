import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Typography,
  Paper,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  CircularProgress,
  Alert
} from '@mui/material'
import api from '../../services/api'

interface Client {
  id: number
  name: string
  type: string
  email: string
  phone: string
  city: string
  state: string
  is_active: boolean
}

export default function ClientList() {
  const navigate = useNavigate()
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchClients()
  }, [])

  const fetchClients = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/v1/clients/clients')
      setClients(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load clients')
    } finally {
      setLoading(false)
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'corporate': return 'primary'
      case 'personal': return 'success'
      case 'government': return 'info'
      default: return 'default'
    }
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Clients</Typography>
        <Button variant="contained" onClick={() => navigate('/clients/new')}>
          Add Client
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      <TableContainer component={Paper}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Email</TableCell>
                <TableCell>Phone</TableCell>
                <TableCell>Location</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {clients.map((client) => (
                <TableRow 
                  key={client.id} 
                  hover
                  onDoubleClick={() => navigate(`/clients/${client.id}`)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>{client.name}</TableCell>
                  <TableCell>
                    <Chip label={client.type} color={getTypeColor(client.type)} size="small" />
                  </TableCell>
                  <TableCell>{client.email}</TableCell>
                  <TableCell>{client.phone}</TableCell>
                  <TableCell>{client.city}, {client.state}</TableCell>
                  <TableCell>
                    <Chip 
                      label={client.is_active ? 'Active' : 'Inactive'} 
                      color={client.is_active ? 'success' : 'default'} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => navigate(`/clients/${client.id}`)}>
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </TableContainer>
    </Box>
  )
}

