/**
 * Payment Override Form
 * Manual payment application for financial flexibility
 */
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import {
  Box,
  Paper,
  TextField,
  Button,
  Grid,
  Typography,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress
} from '@mui/material'
import { Save as SaveIcon } from '@mui/icons-material'
import { useCreatePaymentOverride } from '../hooks/usePaymentMutation'

const paymentOverrideSchema = z.object({
  charter_id: z.number().positive('Charter ID is required'),
  payment_type: z.enum(['check', 'wire', 'cash', 'other']),
  amount: z.number().positive('Amount must be positive'),
  payment_date: z.string().min(1, 'Payment date is required'),
  reference_number: z.string().optional(),
  notes: z.string().optional(),
})

export type PaymentOverrideFormData = z.infer<typeof paymentOverrideSchema>

interface PaymentOverrideFormProps {
  charterId: number
  onSuccess?: () => void
}

export default function PaymentOverrideForm({ charterId, onSuccess }: PaymentOverrideFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PaymentOverrideFormData>({
    resolver: zodResolver(paymentOverrideSchema),
    defaultValues: {
      charter_id: charterId,
      payment_type: 'check',
    }
  })

  const mutation = useCreatePaymentOverride({
    onSuccess: () => {
      onSuccess?.()
    }
  })

  const onSubmit = (data: PaymentOverrideFormData) => {
    mutation.mutate(data)
  }

  if (mutation.isPending) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Manual Payment Application
      </Typography>
      
      {mutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {mutation.error?.response?.data?.detail || 'Failed to apply payment'}
        </Alert>
      )}
      
      <Box component="form" onSubmit={handleSubmit(onSubmit)}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth required>
              <InputLabel>Payment Type</InputLabel>
              <Select
                {...register('payment_type')}
                label="Payment Type"
              >
                <MenuItem value="check">Check</MenuItem>
                <MenuItem value="wire">Wire Transfer</MenuItem>
                <MenuItem value="cash">Cash</MenuItem>
                <MenuItem value="other">Other</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              {...register('amount', { valueAsNumber: true })}
              label="Amount"
              type="number"
              fullWidth
              required
              error={!!errors.amount}
              helperText={errors.amount?.message}
              InputProps={{
                startAdornment: '$',
                inputProps: { min: 0, step: 0.01 }
              }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              {...register('payment_date')}
              label="Payment Date"
              type="date"
              fullWidth
              required
              error={!!errors.payment_date}
              helperText={errors.payment_date?.message}
              InputLabelProps={{ shrink: true }}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              {...register('reference_number')}
              label="Reference Number"
              fullWidth
              error={!!errors.reference_number}
              helperText={errors.reference_number?.message}
              placeholder="Check #, Transaction ID, etc."
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              {...register('notes')}
              label="Notes"
              fullWidth
              multiline
              rows={3}
              error={!!errors.notes}
              helperText={errors.notes?.message}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Box display="flex" gap={2} justifyContent="flex-end">
              <Button
                type="submit"
                variant="contained"
                startIcon={mutation.isPending ? <CircularProgress size={20} /> : <SaveIcon />}
                disabled={mutation.isPending}
              >
                {mutation.isPending ? 'Applying...' : 'Apply Payment'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  )
}
