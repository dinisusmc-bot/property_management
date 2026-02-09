/**
 * Client Payments Tab Component
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
  Tooltip
} from '@mui/material'
import { useQuery } from '@tanstack/react-query'
import api from '@/services/api'
import { format } from 'date-fns'

interface ClientPaymentsTabProps {
  clientId: number
}

export default function ClientPaymentsTab({ clientId }: ClientPaymentsTabProps) {
  const { data: payments, isLoading } = useQuery({
    queryKey: ['client-payments', clientId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/payments?client_id=${clientId}`)
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
      {/* Summary */}
      <Box mb={3} p={2} sx={{ bgcolor: 'background.default', borderRadius: 1 }}>
        <Typography variant="h6">
          Total Paid: ${totalPaid.toLocaleString()}
        </Typography>
      </Box>
      
      {/* Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Date</TableCell>
              <TableCell>Charter Reference</TableCell>
              <TableCell>Payment Method</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Transaction ID</TableCell>
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
                <TableCell>{payment.charter_reference || '-'}</TableCell>
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
                <TableCell>
                  <Tooltip title={payment.transaction_id || 'No transaction ID'}>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                      {payment.transaction_id || '-'}
                    </Typography>
                  </Tooltip>
                </TableCell>
                <TableCell align="center">
                  <Typography variant="body2">View Receipt</Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {payments?.length === 0 && !isLoading && (
        <Box textAlign="center" py={4}>
          <Typography color="text.secondary">
            No payments found for this client
          </Typography>
        </Box>
      )}
    </Box>
  )
}
