import { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material'
import { CheckCircle, Cancel } from '@mui/icons-material'
import { useValidatePromoCode } from '../hooks/usePricing'
import { PromoCode, PromoCodeValidation } from '../types/pricing.types'

interface PromoCodeInputProps {
  amount: number
  onPromoCodeApplied: (promoCode: PromoCode | null) => void
  currentPromoCode?: string
}

export function PromoCodeInput({
  amount,
  onPromoCodeApplied,
  currentPromoCode,
}: PromoCodeInputProps) {
  const [code, setCode] = useState(currentPromoCode || '')
  const [validatedPromoCode, setValidatedPromoCode] = useState<PromoCodeValidation | null>(null)
  const validateMutation = useValidatePromoCode()

  const handleApply = () => {
    if (!code.trim()) return

    validateMutation.mutate(
      { code: code.trim(), amount },
      {
        onSuccess: (validation) => {
          setValidatedPromoCode(validation)
          if (validation.valid && validation.code && validation.discount_value !== undefined) {
            // Convert validation to PromoCode
            onPromoCodeApplied({
              id: validation.promo_code_id || 0,
              code: validation.code,
              description: validation.description || null,
              discount_type: validation.discount_type || 'fixed',
              discount_value: validation.discount_value,
              min_order_value: null,
              max_discount: null,
              valid_from: '',
              valid_until: '',
              is_active: true,
            })
          } else {
            onPromoCodeApplied(null)
          }
        },
        onError: (error: any) => {
          setValidatedPromoCode({
            valid: false,
            message: error.response?.data?.detail || 'Invalid promo code',
          })
          onPromoCodeApplied(null)
        },
      }
    )
  }

  const handleRemove = () => {
    setCode('')
    setValidatedPromoCode(null)
    onPromoCodeApplied(null)
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleApply()
    }
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Promo Code
        </Typography>

        <Box display="flex" gap={1} mb={2}>
          <TextField
            fullWidth
            size="small"
            placeholder="Enter promo code"
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            onKeyPress={handleKeyPress}
            disabled={validateMutation.isPending || !!validatedPromoCode}
          />
          {!validatedPromoCode ? (
            <Button
              variant="contained"
              onClick={handleApply}
              disabled={!code.trim() || validateMutation.isPending}
            >
              {validateMutation.isPending ? <CircularProgress size={24} /> : 'Apply'}
            </Button>
          ) : (
            <Button variant="outlined" color="error" onClick={handleRemove}>
              Remove
            </Button>
          )}
        </Box>

        {/* Valid Promo Code */}
        {validatedPromoCode && validatedPromoCode.valid && (
          <Alert
            severity="success"
            icon={<CheckCircle />}
            sx={{ mb: 2 }}
          >
            <Box>
              <Typography variant="subtitle2">
                {validatedPromoCode.code || code} Applied!
              </Typography>
              {validatedPromoCode.discount_type && validatedPromoCode.discount_value !== undefined && (
                <Typography variant="body2">
                  {validatedPromoCode.discount_type === 'percentage'
                    ? `${validatedPromoCode.discount_value}% off`
                    : `$${validatedPromoCode.discount_value.toFixed(2)} off`}
                </Typography>
              )}
              <Typography variant="body2" color="text.secondary">
                Discount: ${validatedPromoCode.discount_amount?.toFixed(2) || '0.00'}
              </Typography>
              {validatedPromoCode.description && (
                <Typography variant="caption" display="block" mt={1}>
                  {validatedPromoCode.description}
                </Typography>
              )}
            </Box>
          </Alert>
        )}

        {/* Invalid Promo Code */}
        {validatedPromoCode && !validatedPromoCode.valid && (
          <Alert severity="error" icon={<Cancel />} sx={{ mb: 2 }}>
            <Typography variant="body2">
              {validatedPromoCode.message || 'Invalid promo code'}
            </Typography>
          </Alert>
        )}

        {/* Promo code details are shown in the success message above */}
      </CardContent>
    </Card>
  )
}
