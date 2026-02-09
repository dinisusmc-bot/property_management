/**
 * Vendor Management TypeScript Types
 * Aligned with backend schemas
 */

export interface Vendor {
  id: number
  name: string
  company_name: string | null
  email: string
  phone: string
  address: string
  city: string
  state: string
  zip_code: string
  account_status: 'active' | 'suspended' | 'pending'
  total_bookings: number
  total_revenue: number
  outstanding_balance: number
  created_at: string
  updated_at: string | null
}

export interface VendorDetail extends Vendor {
  coi_expiration_date: string | null
  coi_required: boolean
  preferred_payment_method: string | null
  notes: string | null
}

export interface CreateVendorRequest {
  name: string
  company_name?: string
  email: string
  phone: string
  address: string
  city: string
  state: string
  zip_code: string
  coi_required?: boolean
}

export interface UpdateVendorRequest {
  name?: string
  company_name?: string
  email?: string
  phone?: string
  address?: string
  city?: string
  state?: string
  zip_code?: string
  account_status?: 'active' | 'suspended' | 'pending'
  coi_required?: boolean
}

export interface VendorFilter {
  name?: string
  email?: string
  status?: 'active' | 'suspended' | 'pending'
  company_name?: string
}
