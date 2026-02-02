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

interface Vendor {
  id: number
  email: string
  full_name: string
  role: string
  is_active: boolean
  created_at: string
}

export default function VendorList() {
  const navigate = useNavigate()
  const [vendors, setVendors] = useState<Vendor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchVendors()
  }, [])

  const fetchVendors = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/v1/auth/vendors')
      setVendors(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load vendors')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3 }}>
        <Typography variant="h4">Vendors</Typography>
        <Button variant="contained" onClick={() => navigate('/users/new')}>
          Add Vendor
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
                <TableCell>Email</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {vendors.map((vendor) => (
                <TableRow 
                  key={vendor.id} 
                  hover
                  onDoubleClick={() => navigate(`/vendors/${vendor.id}`)}
                  sx={{ cursor: 'pointer' }}
                >
                  <TableCell>{vendor.full_name}</TableCell>
                  <TableCell>{vendor.email}</TableCell>
                  <TableCell>
                    <Chip 
                      label={vendor.is_active ? 'Active' : 'Inactive'} 
                      color={vendor.is_active ? 'success' : 'default'} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell>{formatDate(vendor.created_at)}</TableCell>
                  <TableCell>
                    <Button size="small" onClick={() => navigate(`/vendors/${vendor.id}`)}>
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
