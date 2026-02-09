/**
 * Client Portal Query Hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clientPortalApi } from '../api/client-portal-api'
import toast from 'react-hot-toast'

export function useClientLogin() {
  return useMutation({
    mutationFn: clientPortalApi.login,
    onSuccess: (data) => {
      if (data.success) {
        toast.success('Login successful')
      } else {
        toast.error(data.message || 'Login failed')
      }
    },
    onError: () => {
      toast.error('Failed to login')
    }
  })
}

export function useClientLogout() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: clientPortalApi.logout,
    onSuccess: () => {
      queryClient.clear()
      toast.success('Logged out successfully')
    }
  })
}

export function useClientProfile() {
  return useQuery({
    queryKey: ['client-profile'],
    queryFn: clientPortalApi.getProfile,
    enabled: false, // Only fetch when logged in
  })
}

export function useClientBookings() {
  return useQuery({
    queryKey: ['client-bookings'],
    queryFn: clientPortalApi.getBookings,
  })
}

export function useClientPayments() {
  return useQuery({
    queryKey: ['client-payments'],
    queryFn: clientPortalApi.getPayments,
  })
}

export function useCreateBooking() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: any) => clientPortalApi.createBooking(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-bookings'] })
      toast.success('Booking created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create booking')
    }
  })
}

export function useCancelBooking() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (bookingId: number) => clientPortalApi.cancelBooking(bookingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-bookings'] })
      toast.success('Booking cancelled successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to cancel booking')
    }
  })
}

export function useGetQuote() {
  return useMutation({
    mutationFn: (data: any) => clientPortalApi.getQuote(data),
  })
}
