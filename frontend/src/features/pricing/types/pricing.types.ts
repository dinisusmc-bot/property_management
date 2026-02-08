export interface PricingRequest {
  client_id: number
  vehicle_id: number
  passengers: number
  trip_date: string
  total_miles: number
  trip_hours: number
  is_overnight?: boolean
  is_weekend?: boolean
  is_holiday?: boolean
  additional_fees?: number
  notes?: string
}

export interface PricingBreakdown {
  base_cost: number
  mileage_cost: number
  time_based_cost: number
  weekend_multiplier: number
  overnight_multiplier: number
  holiday_multiplier: number
  seasonal_multiplier: number
  additional_fees: number
  fuel_surcharge: number
  subtotal: number
  total_cost: number
  rules_applied: number[]
  calculation_notes?: string | null
}

export interface PricingResponse {
  calculation_id?: number | null
  breakdown: PricingBreakdown
  expires_at?: string | null
  dot_compliant?: boolean
}

export interface PricingLineItem {
  description: string
  amount: number
}

export interface PromoCode {
  id: number
  code: string
  description?: string | null
  discount_type: 'percentage' | 'fixed'
  discount_value: number
  min_order_value: number | null
  max_discount: number | null
  valid_from: string
  valid_until: string
  usage_limit?: number | null
  usage_count?: number
  is_active: boolean
}

export interface PromoCodeValidation {
  valid: boolean
  message?: string
  promo_code_id?: number
  code?: string
  description?: string | null
  discount_type?: 'percentage' | 'fixed'
  discount_value?: number
  order_value?: number
  discount?: number
  discount_amount?: number
  final_amount?: number
}

export interface Amenity {
  id: number
  name: string
  description?: string | null
  price: number
  category?: string | null
  is_active: boolean
}

export interface DOTCompliance {
  compliant: boolean
  violations: string[]
  warnings: string[]
  estimated_hours: {
    driving_hours: number
    stop_time_hours: number
    inspection_hours: number
    post_trip_hours: number
    total_duty_hours: number
    calculated_from_distance: boolean
  }
  requires_second_driver: boolean
  max_daily_driving: number
  max_daily_duty: number
  minimum_rest_required_hours?: number
  earliest_next_trip?: string
}
