import api from '@/services/api'
import { PricingRequest, PricingResponse, PromoCode, PromoCodeValidation, Amenity, DOTCompliance } from '../types/pricing.types'

export const pricingApi = {
  // Calculate quote pricing
  calculateQuote: async (request: PricingRequest) => {
    const response = await api.post<PricingResponse>('/api/v1/pricing/calculate-quote', request)
    return response.data
  },
  
  // Validate promo code
  validatePromoCode: async (code: string, amount: number) => {
    const response = await api.post<PromoCodeValidation>('/api/v1/pricing/promo-codes/validate', null, {
      params: {
        code,
        order_value: amount
      }
    })
    return response.data
  },
  
  // Get available amenities
  getAmenities: async () => {
    const response = await api.get<Amenity[]>('/api/v1/pricing/amenities')
    return response.data
  },
  
  // Check DOT compliance
  checkDOTCompliance: async (params: {
    distance_miles: number
    stops_count?: number
    trip_hours?: number
    is_multi_day?: boolean
    driver_hours_this_week?: number
  }) => {
    const response = await api.post<DOTCompliance>('/api/v1/pricing/check-dot-compliance', null, {
      params
    })
    return response.data
  },
  
  // Get all active promo codes (admin only)
  getPromoCodes: async () => {
    const response = await api.get<PromoCode[]>('/api/v1/pricing/promo-codes')
    return response.data
  }
}
