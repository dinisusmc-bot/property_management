/**
 * Client Portal API Service
 */
import api from '@/services/api'
import { ClientAuthRequest, ClientAuthResponse, ClientProfile, ClientBooking, ClientPayment } from '../types/client-portal.types'

export const clientPortalApi = {
  login: async (credentials: ClientAuthRequest) => {
    const response = await api.post<ClientAuthResponse>('/api/v1/client-portal/login', credentials)
    return response.data
  },
  
  logout: async () => {
    const response = await api.post('/api/v1/client-portal/logout')
    return response.data
  },
  
  getProfile: async () => {
    const response = await api.get<ClientProfile>('/api/v1/client-portal/profile')
    return response.data
  },
  
  getBookings: async () => {
    const response = await api.get<ClientBooking[]>('/api/v1/client-portal/bookings')
    return response.data
  },
  
  getPayments: async () => {
    const response = await api.get<ClientPayment[]>('/api/v1/client-portal/payments')
    return response.data
  },
  
  createBooking: async (data: {
    pickup_location: string
    dropoff_location: string
    pickup_date: string
    pickup_time: string
    passengers: number
    vehicle_type: string
    notes?: string
  }) => {
    const response = await api.post<ClientBooking>('/api/v1/client-portal/bookings', data)
    return response.data
  },
  
  cancelBooking: async (bookingId: number) => {
    const response = await api.post(`/api/v1/client-portal/bookings/${bookingId}/cancel`)
    return response.data
  },
  
  getQuote: async (data: {
    pickup_location: string
    dropoff_location: string
    pickup_date: string
    pickup_time: string
    passengers: number
  }) => {
    const response = await api.post('/api/v1/client-portal/quote', data)
    return response.data
  }
}
