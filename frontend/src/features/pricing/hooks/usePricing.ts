import { useQuery, useMutation } from '@tanstack/react-query'
import { pricingApi } from '../api/pricingApi'
import { PricingRequest } from '../types/pricing.types'
import toast from 'react-hot-toast'

// Query Keys
export const pricingKeys = {
  all: ['pricing'] as const,
  amenities: () => [...pricingKeys.all, 'amenities'] as const,
  promoCodes: () => [...pricingKeys.all, 'promo-codes'] as const,
  quote: (request: PricingRequest) => [...pricingKeys.all, 'quote', request] as const,
}

// Get amenities
export function useAmenities() {
  return useQuery({
    queryKey: pricingKeys.amenities(),
    queryFn: () => pricingApi.getAmenities(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Get promo codes (admin only)
export function usePromoCodes() {
  return useQuery({
    queryKey: pricingKeys.promoCodes(),
    queryFn: () => pricingApi.getPromoCodes(),
    staleTime: 2 * 60 * 1000,
  })
}

// Calculate quote pricing
export function useCalculateQuote() {
  return useMutation({
    mutationFn: (request: PricingRequest) => pricingApi.calculateQuote(request),
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to calculate pricing')
    },
  })
}

// Validate promo code
export function useValidatePromoCode() {
  return useMutation({
    mutationFn: ({ code, amount }: { code: string; amount: number }) =>
      pricingApi.validatePromoCode(code, amount),
    onSuccess: (data) => {
      if (data.valid) {
        const discount = data.discount ?? data.discount_amount ?? 0
        toast.success(`Promo code applied! Discount: $${discount.toFixed(2)}`)
      } else {
        toast.error(data.message || 'Invalid promo code')
      }
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to validate promo code')
    },
  })
}

// Check DOT compliance
export function useCheckDOTCompliance() {
  return useMutation({
    mutationFn: (params: {
      distance_miles: number
      stops_count?: number
      trip_hours?: number
      is_multi_day?: boolean
      driver_hours_this_week?: number
    }) => pricingApi.checkDOTCompliance(params),
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to check DOT compliance')
    },
  })
}
