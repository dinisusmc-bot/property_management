/**
 * Client Management TypeScript Types
 * Aligned with backend schemas
 */

export interface Client {
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

export interface ClientDetail extends Client {
  notes: string | null
  coi_expiration_date: string | null
  coi_required: boolean
  preferred_payment_method: string | null
  billing_address: string
}

export interface CreateClientRequest {
  name: string
  company_name?: string
  email: string
  phone: string
  address: string
  city: string
  state: string
  zip_code: string
  coi_required?: boolean
  billing_address?: string
}

export interface UpdateClientRequest {
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
  billing_address?: string
}

export interface ClientFilter {
  name?: string
  email?: string
  status?: 'active' | 'suspended' | 'pending'
  company_name?: string
}
