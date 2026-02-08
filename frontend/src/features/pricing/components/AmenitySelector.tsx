import {
  Box,
  Card,
  CardContent,
  Typography,
  FormGroup,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material'
import { useAmenities } from '../hooks/usePricing'
import { Amenity } from '../types/pricing.types'

interface AmenitySelectorProps {
  selectedAmenities: string[]
  onChange: (amenities: string[]) => void
}

export function AmenitySelector({ selectedAmenities, onChange }: AmenitySelectorProps) {
  const { data: amenities, isLoading, isError } = useAmenities()

  const handleToggle = (amenityId: string) => {
    if (selectedAmenities.includes(amenityId)) {
      onChange(selectedAmenities.filter(id => id !== amenityId))
    } else {
      onChange([...selectedAmenities, amenityId])
    }
  }

  const calculateTotal = () => {
    if (!amenities) return 0
    return amenities
      .filter((a: Amenity) => selectedAmenities.includes(a.id.toString()))
      .reduce((sum: number, a: Amenity) => sum + a.price, 0)
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2}>
            <CircularProgress size={24} />
            <Typography>Loading amenities...</Typography>
          </Box>
        </CardContent>
      </Card>
    )
  }

  if (isError || !amenities) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">Failed to load amenities</Alert>
        </CardContent>
      </Card>
    )
  }

  const total = calculateTotal()

  return (
    <Card>
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">Amenities</Typography>
          {total > 0 && (
            <Chip
              label={`+$${total.toFixed(2)}`}
              color="primary"
              size="small"
            />
          )}
        </Box>

        <FormGroup>
          {amenities.map((amenity: Amenity) => (
            <FormControlLabel
              key={amenity.id}
              control={
                <Checkbox
                  checked={selectedAmenities.includes(amenity.id.toString())}
                  onChange={() => handleToggle(amenity.id.toString())}
                  disabled={!amenity.is_active}
                />
              }
              label={
                <Box display="flex" justifyContent="space-between" width="100%">
                  <Box>
                    <Typography variant="body2">{amenity.name}</Typography>
                    {amenity.description && (
                      <Typography variant="caption" color="text.secondary">
                        {amenity.description}
                      </Typography>
                    )}
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    ${amenity.price.toFixed(2)}
                  </Typography>
                </Box>
              }
            />
          ))}
        </FormGroup>

        {amenities.length === 0 && (
          <Typography color="text.secondary" variant="body2">
            No amenities available
          </Typography>
        )}
      </CardContent>
    </Card>
  )
}
