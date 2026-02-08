export interface CharterTemplate {
  id: number
  template_name: string
  is_multi_vehicle: boolean
  total_vehicles: number
  passengers: number
  trip_hours: number
  created_at: string | null
}

export interface CloneCharterRequest {
  charter_id: number
  trip_date: string
  client_id?: number
  overrides?: Record<string, any>
}

export interface RecurringCharterRequest {
  series_name: string
  client_id: number
  description?: string
  recurrence_pattern: 'daily' | 'weekly' | 'monthly'
  recurrence_days?: string
  start_date: string
  end_date?: string
  template_charter_id: number
  generate_charters?: boolean
}

export interface CreateTemplateRequest {
  charter_id: number
  template_name: string
}

export interface ApplyTemplateRequest {
  template_id: number
  trip_date: string
  client_id?: number
  overrides?: Record<string, any>
}
