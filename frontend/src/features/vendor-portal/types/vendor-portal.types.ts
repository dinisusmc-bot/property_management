/**
 * Vendor Portal Types
 */
export interface VendorAuthRequest {
  email: string
  password: string
}

export interface VendorAuthResponse {
  success: boolean
  message?: string
  vendor?: any
  token?: string
}

export interface VendorProfile {
  id: number
  name: string
  company_name: string
  email: string
  phone: string
  address: string
  city: string
  state: string
  zip_code: string
  coi_expiration_date: string | null
  coi_required: boolean
  created_at: string
}

export interface VendorBid {
  id: number
  charter_id: number
  vendor_id: number
  amount: number
  status: 'pending' | 'accepted' | 'rejected' | 'expired'
  created_at: string
  updated_at: string | null
}

export interface VendorTrip {
  id: number
  reference_number: string
  client_name: string
  pickup_date: string
  pickup_location: string
  dropoff_location: string
  passengers: number
  status: string
  amount: number
}
