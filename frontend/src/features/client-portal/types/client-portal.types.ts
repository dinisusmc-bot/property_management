/**
 * Client Portal Types
 */
export interface ClientAuthRequest {
  email: string
  password: string
}

export interface ClientAuthResponse {
  success: boolean
  message?: string
  client?: any
  token?: string
}

export interface ClientProfile {
  id: number
  name: string
  company_name: string | null
  email: string
  phone: string
  address: string
  city: string
  state: string
  zip_code: string
  created_at: string
}

export interface ClientBooking {
  id: number
  reference_number: string
  pickup_date: string
  pickup_time: string
  pickup_location: string
  dropoff_location: string
  passengers: number
  vehicle_type: string
  total_price: number
  balance_due: number
  status: string
}

export interface ClientPayment {
  id: number
  charter_id: number
  amount: number
  payment_date: string
  payment_method: string
  payment_status: string
}
