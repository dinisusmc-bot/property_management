/**
 * Dispatch Types
 */
export interface DispatchTrip {
  id: number
  reference_number: string
  client_name: string
  pickup_date: string
  pickup_time: string
  pickup_location: string
  dropoff_location: string
  passengers: number
  vehicle_type: string
  vendor_id: number | null
  vendor_name: string | null
  driver_id: number | null
  driver_name: string | null
  status: 'unassigned' | 'assigned' | 'in_transit' | 'completed' | 'cancelled'
  priority: 'low' | 'normal' | 'high' | 'urgent'
  notes: string | null
}

export interface DispatchDriver {
  id: number
  name: string
  phone: string
  vendor_id: number
  vendor_name: string
  current_location: {
    latitude: number
    longitude: number
  } | null
  status: 'available' | 'assigned' | 'in_transit' | 'off_duty'
  assigned_trips_today: number
}

export interface DispatchFilters {
  date?: string
  status?: string
  vendor_id?: number
  priority?: string
}
