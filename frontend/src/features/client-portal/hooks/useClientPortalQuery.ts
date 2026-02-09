/**
 * Client Portal Query Hooks
 * React Query hooks for client portal features
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../../../services/api'

// Booking queries
export function useClientBookings() {
  return useQuery({
    queryKey: ['client-portal', 'bookings'],
    queryFn: async () => {
      const response = await api.get('/api/v1/client/bookings')
      return response.data
    }
  })
}

export function useCreateBooking() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async (bookingData: any) => {
      const response = await api.post('/api/v1/client/bookings', bookingData)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-portal', 'bookings'] })
    }
  })
}

// Payment queries
export function useClientPayments() {
  return useQuery({
    queryKey: ['client-portal', 'payments'],
    queryFn: async () => {
      const response = await api.get('/api/v1/client/payments')
      return response.data
    }
  })
}

// Client profile queries
export function useClientProfile() {
  return useQuery({
    queryKey: ['client-portal', 'profile'],
    queryFn: async () => {
      const response = await api.get('/api/v1/client/profile')
      return response.data
    }
  })
}

// Client documents queries
export function useClientDocuments() {
  return useQuery({
    queryKey: ['client-portal', 'documents'],
    queryFn: async () => {
      const response = await api.get('/api/v1/client/documents')
      return response.data
    }
  })
}

// Client trips queries
export function useClientTrips() {
  return useQuery({
    queryKey: ['client-portal', 'trips'],
    queryFn: async () => {
      const response = await api.get('/api/v1/client/trips')
      return response.data
    }
  })
}
