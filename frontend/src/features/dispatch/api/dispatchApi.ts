/**
 * Dispatch API Service
 */
import api from '@/services/api'
import { DispatchTrip, DispatchDriver, DispatchFilters } from '../types/dispatch.types'

export const dispatchApi = {
  getTrips: async (filters?: DispatchFilters) => {
    const params = new URLSearchParams()
    if (filters?.date) params.append('date', filters.date)
    if (filters?.status) params.append('status', filters.status)
    if (filters?.vendor_id) params.append('vendor_id', filters.vendor_id.toString())
    if (filters?.priority) params.append('priority', filters.priority)
    
    const response = await api.get<DispatchTrip[]>(`/api/v1/dispatch/trips?${params}`)
    return response.data
  },
  
  getDrivers: async () => {
    const response = await api.get<DispatchDriver[]>('/api/v1/dispatch/drivers')
    return response.data
  },
  
  assignDriver: async (tripId: number, driverId: number) => {
    const response = await api.post(`/api/v1/dispatch/trips/${tripId}/assign`, {
      driver_id: driverId
    })
    return response.data
  },
  
  unassignDriver: async (tripId: number) => {
    const response = await api.post(`/api/v1/dispatch/trips/${tripId}/unassign`)
    return response.data
  },
  
  updateTripStatus: async (tripId: number, status: string) => {
    const response = await api.patch(`/api/v1/dispatch/trips/${tripId}/status`, { status })
    return response.data
  },
  
  updatePriority: async (tripId: number, priority: string) => {
    const response = await api.patch(`/api/v1/dispatch/trips/${tripId}/priority`, { priority })
    return response.data
  }
}
