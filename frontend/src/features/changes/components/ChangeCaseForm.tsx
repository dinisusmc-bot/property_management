/**
 * Change Case Form - Create and edit change cases
 */
import { useEffect } from 'react'
import { useForm, Controller } from 'react-hook-form'
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
  FormHelperText,
  FormControlLabel,
  Checkbox
} from '@mui/material'
import { Save as SaveIcon } from '@mui/icons-material'
import { ChangeType, ChangePriority, ImpactLevel, type CreateChangeCaseRequest } from '../types/change.types'
import { useCreateChangeCase } from '../hooks/useChangeMutation'

const changeCaseSchema = z.object({
  charter_id: z.number().positive('Charter ID is required'),
  client_id: z.number().positive('Client ID is required'),
  vendor_id: z.number().nullable().optional(),
  change_type: z.nativeEnum(ChangeType),
  priority: z.nativeEnum(ChangePriority),
  title: z.string().min(1, 'Title is required').max(200),
  description: z.string().min(1, 'Description is required'),
  reason: z.string().min(1, 'Reason is required'),
  impact_level: z.nativeEnum(ImpactLevel),
  impact_assessment: z.string().optional(),
  affects_vendor: z.boolean(),
  affects_pricing: z.boolean(),
  affects_schedule: z.boolean(),
  current_price: z.number().nullable().optional(),
  proposed_price: z.number().nullable().optional(),
  due_date: z.string().optional(),
})

type ChangeCaseFormData = z.infer<typeof changeCaseSchema>

interface ChangeCaseFormProps {
  charterId?: number
  clientId?: number
  onSuccess?: () => void
}

export default function ChangeCaseForm({ charterId, clientId, onSuccess }: ChangeCaseFormProps) {
  const createMutation = useCreateChangeCase()

  const {
    register,
    handleSubmit,
    control,
    watch,
    setValue,
    formState: { errors }
  } = useForm<ChangeCaseFormData>({
    resolver: zodResolver(changeCaseSchema),
    defaultValues: {
      charter_id: charterId || 0,
      client_id: clientId || 0,
      vendor_id: null,
      change_type: ChangeType.OTHER,
      priority: ChangePriority.MEDIUM,
      impact_level: ImpactLevel.MINIMAL,
      affects_vendor: false,
      affects_pricing: false,
      affects_schedule: false,
      current_price: null,
      proposed_price: null,
    }
  })

  // Watch affects_pricing to conditionally show price fields
  const affectsPricing = watch('affects_pricing')

  useEffect(() => {
    if (charterId) setValue('charter_id', charterId)
    if (clientId) setValue('client_id', clientId)
  }, [charterId, clientId, setValue])

  const onSubmit = (data: ChangeCaseFormData) => {
    const request: CreateChangeCaseRequest = {
      ...data,
      requested_by: 1, // TODO: Get from auth context
      requested_by_name: 'Admin User', // TODO: Get from auth context
    }

    createMutation.mutate(request, {
      onSuccess: () => {
        onSuccess?.()
      }
    })
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Create Change Case
      </Typography>
      
      <Box component="form" onSubmit={handleSubmit(onSubmit)}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              {...register('charter_id', { valueAsNumber: true })}
              label="Charter ID"
              type="number"
              fullWidth
              required
              error={!!errors.charter_id}
              helperText={errors.charter_id?.message}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              {...register('client_id', { valueAsNumber: true })}
              label="Client ID"
              type="number"
              fullWidth
              required
              error={!!errors.client_id}
              helperText={errors.client_id?.message}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              {...register('title')}
              label="Title"
              fullWidth
              required
              error={!!errors.title}
              helperText={errors.title?.message}
              inputProps={{ maxLength: 200 }}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth required error={!!errors.change_type}>
              <InputLabel>Change Type</InputLabel>
              <Controller
                name="change_type"
                control={control}
                render={({ field }) => (
                  <Select {...field} label="Change Type">
                    {Object.values(ChangeType).map((type) => (
                      <MenuItem key={type} value={type}>
                        {type.replace(/_/g, ' ').toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                )}
              />
              {errors.change_type && (
                <FormHelperText>{errors.change_type.message}</FormHelperText>
              )}
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth required error={!!errors.priority}>
              <InputLabel>Priority</InputLabel>
              <Controller
                name="priority"
                control={control}
                render={({ field }) => (
                  <Select {...field} label="Priority">
                    {Object.values(ChangePriority).map((priority) => (
                      <MenuItem key={priority} value={priority}>
                        {priority.toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                )}
              />
              {errors.priority && (
                <FormHelperText>{errors.priority.message}</FormHelperText>
              )}
            </FormControl>
          </Grid>

          <Grid item xs={12}>
            <TextField
              {...register('description')}
              label="Description"
              multiline
              rows={4}
              fullWidth
              required
              error={!!errors.description}
              helperText={errors.description?.message}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              {...register('reason')}
              label="Reason for Change"
              multiline
              rows={3}
              fullWidth
              required
              error={!!errors.reason}
              helperText={errors.reason?.message}
            />
          </Grid>

          <Grid item xs={12} md={6}>
            <FormControl fullWidth required error={!!errors.impact_level}>
              <InputLabel>Impact Level</InputLabel>
              <Controller
                name="impact_level"
                control={control}
                render={({ field }) => (
                  <Select {...field} label="Impact Level">
                    {Object.values(ImpactLevel).map((level) => (
                      <MenuItem key={level} value={level}>
                        {level.toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                )}
              />
              {errors.impact_level && (
                <FormHelperText>{errors.impact_level.message}</FormHelperText>
              )}
            </FormControl>
          </Grid>

          <Grid item xs={12} md={6}>
            <TextField
              {...register('due_date')}
              label="Due Date"
              type="date"
              fullWidth
              InputLabelProps={{ shrink: true }}
              error={!!errors.due_date}
              helperText={errors.due_date?.message}
            />
          </Grid>

          <Grid item xs={12}>
            <TextField
              {...register('impact_assessment')}
              label="Impact Assessment"
              multiline
              rows={2}
              fullWidth
              placeholder="Optional detailed impact analysis"
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <Controller
              name="affects_vendor"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={<Checkbox {...field} checked={field.value} />}
                  label="Affects Vendor"
                />
              )}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <Controller
              name="affects_pricing"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={<Checkbox {...field} checked={field.value} />}
                  label="Affects Pricing"
                />
              )}
            />
          </Grid>

          <Grid item xs={12} md={4}>
            <Controller
              name="affects_schedule"
              control={control}
              render={({ field }) => (
                <FormControlLabel
                  control={<Checkbox {...field} checked={field.value} />}
                  label="Affects Schedule"
                />
              )}
            />
          </Grid>

          {affectsPricing && (
            <>
              <Grid item xs={12} md={6}>
                <TextField
                  {...register('current_price', { valueAsNumber: true })}
                  label="Current Price"
                  type="number"
                  fullWidth
                  InputProps={{
                    startAdornment: '$',
                    inputProps: { min: 0, step: 0.01 }
                  }}
                  error={!!errors.current_price}
                  helperText={errors.current_price?.message}
                />
              </Grid>

              <Grid item xs={12} md={6}>
                <TextField
                  {...register('proposed_price', { valueAsNumber: true })}
                  label="Proposed Price"
                  type="number"
                  fullWidth
                  InputProps={{
                    startAdornment: '$',
                    inputProps: { min: 0, step: 0.01 }
                  }}
                  error={!!errors.proposed_price}
                  helperText={errors.proposed_price?.message}
                />
              </Grid>
            </>
          )}

          <Grid item xs={12}>
            <Box display="flex" gap={2} justifyContent="flex-end">
              <Button
                type="submit"
                variant="contained"
                startIcon={<SaveIcon />}
                disabled={createMutation.isPending}
              >
                {createMutation.isPending ? 'Creating...' : 'Create Change Case'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Paper>
  )
}
