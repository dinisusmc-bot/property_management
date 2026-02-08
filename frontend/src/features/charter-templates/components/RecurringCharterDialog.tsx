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
  Chip,
  RadioGroup,
  Radio,
  FormControl,
  FormLabel,
  FormControlLabel,
} from '@mui/material'
import { useCreateRecurringCharters } from '../hooks/useTemplates'
import { format, addMonths } from 'date-fns'

interface RecurringCharterDialogProps {
  open: boolean
  onClose: () => void
  charterId: number
  clientId: number
  currentTripDate: string
}

export function RecurringCharterDialog({
  open,
  onClose,
  charterId,
  clientId,
  currentTripDate,
}: RecurringCharterDialogProps) {
  const [startDate, setStartDate] = useState(format(new Date(currentTripDate), 'yyyy-MM-dd'))
  const [endDate, setEndDate] = useState(
    format(addMonths(new Date(currentTripDate), 3), 'yyyy-MM-dd')
  )
  const [pattern, setPattern] = useState<'daily' | 'weekly' | 'monthly'>('weekly')
  const [selectedDays, setSelectedDays] = useState<number[]>([1, 3, 5]) // Mon, Wed, Fri

  const recurringMutation = useCreateRecurringCharters()

  const daysOfWeek = [
    { value: 1, label: 'Mon' },
    { value: 2, label: 'Tue' },
    { value: 3, label: 'Wed' },
    { value: 4, label: 'Thu' },
    { value: 5, label: 'Fri' },
    { value: 6, label: 'Sat' },
    { value: 7, label: 'Sun' },
  ]

  const dayLabelMap: Record<number, string> = {
    1: 'mon',
    2: 'tue',
    3: 'wed',
    4: 'thu',
    5: 'fri',
    6: 'sat',
    7: 'sun',
  }

  const toggleDay = (day: number) => {
    if (selectedDays.includes(day)) {
      setSelectedDays(selectedDays.filter((d) => d !== day))
    } else {
      setSelectedDays([...selectedDays, day].sort())
    }
  }

  const handleSubmit = () => {
    const recurrenceDays =
      pattern === 'weekly'
        ? selectedDays.map((d) => dayLabelMap[d]).join(',')
        : undefined

    recurringMutation.mutate(
      {
        series_name: `Recurring Charter ${charterId}`,
        client_id: clientId,
        description: `Generated from charter ${charterId}`,
        start_date: startDate,
        end_date: endDate,
        recurrence_pattern: pattern,
        recurrence_days: recurrenceDays,
        template_charter_id: charterId,
        generate_charters: true,
      },
      {
        onSuccess: () => {
          onClose()
        },
      }
    )
  }

  const getPreviewText = () => {
    if (pattern === 'daily') {
      return 'Every day'
    }
    if (pattern === 'weekly') {
      const days = selectedDays.map((d) => daysOfWeek.find((dow) => dow.value === d)?.label)
      return `Every week on ${days.join(', ')}`
    }
    return 'Every month'
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Create Recurring Charters</DialogTitle>
      <DialogContent>
        <Box mt={2}>
          <Alert severity="info" sx={{ mb: 3 }}>
            Create multiple charters with a recurring schedule
          </Alert>

          {/* Date Range */}
          <Box display="grid" gridTemplateColumns="1fr 1fr" gap={2} mb={3}>
            <TextField
              fullWidth
              type="date"
              label="Start Date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              fullWidth
              type="date"
              label="End Date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Box>

          {/* Recurrence Pattern */}
          <FormControl component="fieldset" sx={{ mb: 3 }}>
            <FormLabel>Recurrence Pattern</FormLabel>
            <RadioGroup row value={pattern} onChange={(e) => setPattern(e.target.value as any)}>
              <FormControlLabel value="daily" control={<Radio />} label="Daily" />
              <FormControlLabel value="weekly" control={<Radio />} label="Weekly" />
              <FormControlLabel value="monthly" control={<Radio />} label="Monthly" />
            </RadioGroup>
          </FormControl>

          {/* Days of Week (for weekly pattern) */}
          {pattern === 'weekly' && (
            <Box mb={3}>
              <Typography variant="subtitle2" gutterBottom>
                Repeat on days:
              </Typography>
              <Box display="flex" gap={1} flexWrap="wrap">
                {daysOfWeek.map((day) => (
                  <Chip
                    key={day.value}
                    label={day.label}
                    onClick={() => toggleDay(day.value)}
                    color={selectedDays.includes(day.value) ? 'primary' : 'default'}
                    variant={selectedDays.includes(day.value) ? 'filled' : 'outlined'}
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Preview */}
          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="subtitle2">Schedule Preview</Typography>
            <Typography variant="body2">{getPreviewText()}</Typography>
            <Typography variant="caption" color="text.secondary">
              From {format(new Date(startDate), 'MMM dd, yyyy')} to{' '}
              {format(new Date(endDate), 'MMM dd, yyyy')}
            </Typography>
          </Alert>

        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={recurringMutation.isPending}>
          Cancel
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={
            !startDate ||
            !endDate ||
            (pattern === 'weekly' && selectedDays.length === 0) ||
            recurringMutation.isPending
          }
        >
          {recurringMutation.isPending ? 'Creating...' : 'Create Recurring Charters'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
