export interface Lead {
  id: number
  first_name: string
  last_name: string
  name?: string | null
  company_name: string | null
  email: string
  phone: string | null
  source: 'web' | 'phone' | 'email' | 'referral' | 'walk_in' | 'partner'
  status: 'new' | 'contacted' | 'qualified' | 'negotiating' | 'converted' | 'dead'
  assigned_agent_id: number | null
  assigned_at: string | null
  trip_details: string | null
  estimated_passengers: number | null
  estimated_trip_date: string | null
  pickup_location: string | null
  dropoff_location: string | null
  last_contact_date?: string | null
  trip_type?: string | null
  trip_date?: string | null
  passengers?: number | null
  notes?: string | null
  converted_to_client_id: number | null
  converted_to_charter_id: number | null
  converted_at: string | null
  score: number
  priority: string
  next_follow_up_date: string | null
  follow_up_count: number
  created_at: string
  updated_at: string | null
}

export interface CreateLeadRequest {
  first_name: string
  last_name: string
  company_name?: string
  email: string
  phone?: string
  source: string
  trip_details?: string
  estimated_passengers?: number
  estimated_trip_date?: string
  pickup_location?: string
  dropoff_location?: string
}

export interface UpdateLeadRequest {
  first_name?: string
  last_name?: string
  company_name?: string
  email?: string
  phone?: string
  status?: string
  trip_details?: string
  estimated_passengers?: number
  estimated_trip_date?: string
  pickup_location?: string
  dropoff_location?: string
  next_follow_up_date?: string
  priority?: string
}

export interface LeadFilters {
  status?: string
  source?: string
  assigned_to?: number
  search?: string
  date_from?: string
  date_to?: string
}
