/**
 * Client Payment History Tab Component
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
  Card,
  CardContent
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import api from '../../../services/api'
import { format } from 'date-fns'

export default function ClientPaymentHistory() {
  const { data: payments, isLoading } = useQuery({
    queryKey: ['client-portal', 'payments'],
    queryFn: async () => {
      const response = await api.get('/api/v1/client/payments')
      return response.data
    }
  })
  
  const getPaymentStatusColor = (status: string) => {
    const colors: Record<string, any> = {
      completed: 'success',
      pending: 'warning',
      failed: 'error',
      refunded: 'default'
    }
    return colors[status] || 'default'
  }
  
  const totalPaid = payments?.reduce((sum: number, p: any) => sum + (p.amount || 0), 0) || 0

  if (isLoading) {
    return <Typography>Loading...</Typography>
  }

  return (
    <Box>
      {/* Summary Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Payment Summary
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total Paid: ${totalPaid.toLocaleString()}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Transactions: {payments?.length || 0}
          </Typography>
        </CardContent>
      </Card>
      
      {/* Payment Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Booking Reference</TableCell>
              <TableCell>Method</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="center">Receipt</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {payments?.map((payment: any) => (
              <TableRow key={payment.id} hover>
                <TableCell>
                  {payment.payment_date 
                    ? format(new Date(payment.payment_date), 'MMM dd, yyyy HH:mm')
                    : '-'}
                </TableCell>
                <TableCell>{payment.charter_reference || `#${payment.charter_id}`}</TableCell>
                <TableCell>
                  <Chip label={payment.payment_method || 'N/A'} size="small" />
                </TableCell>
                <TableCell align="right">
                  ${payment.amount?.toFixed(2) || '0.00'}
                </TableCell>
                <TableCell>
                  <Chip
                    label={payment.payment_status || 'unknown'}
                    color={getPaymentStatusColor(payment.payment_status || '')}
                    size="small"
                  />
                </TableCell>
                <TableCell align="center">
                  {payment.receipt_url ? (
                    <Chip
                      label="View"
                      color="primary"
                      size="small"
                      sx={{ cursor: 'pointer' }}
                      onClick={() => window.open(payment.receipt_url, '_blank')}
                    />
                  ) : (
                    <Typography variant="body2" color="text.secondary">-</Typography>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {payments?.length === 0 && !isLoading && (
        <Box textAlign="center" py={4}>
          <Typography color="text.secondary">
            No payment history found
          </Typography>
          <Typography variant="body2" sx={{ mt: 1 }}>
            Your first booking will appear here
          </Typography>
        </Box>
      )}
    </Box>
  )
}
