/**
 * Vendor Portal Query Hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { vendorPortalApi } from '../api/vendor-portal-api'
import toast from 'react-hot-toast'

export function useVendorLogin() {
  return useMutation({
    mutationFn: vendorPortalApi.login,
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

export function useVendorLogout() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: vendorPortalApi.logout,
    onSuccess: () => {
      queryClient.clear()
      toast.success('Logged out successfully')
    }
  })
}

export function useVendorProfile() {
  return useQuery({
    queryKey: ['vendor-profile'],
    queryFn: vendorPortalApi.getProfile,
    enabled: false, // Only fetch when logged in
  })
}

export function useVendorBids() {
  return useQuery({
    queryKey: ['vendor-bids'],
    queryFn: vendorPortalApi.getBids,
  })
}

export function useVendorTrips() {
  return useQuery({
    queryKey: ['vendor-trips'],
    queryFn: vendorPortalApi.getTrips,
  })
}

export function useSubmitBid() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ charterId, amount }: { charterId: number; amount: number }) => 
      vendorPortalApi.submitBid(charterId, amount),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-bids'] })
      toast.success('Bid submitted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to submit bid')
    }
  })
}

export function useUpdateCOI() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (file: File) => vendorPortalApi.updateCOI(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendor-profile'] })
      toast.success('COI updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update COI')
    }
  })
}
