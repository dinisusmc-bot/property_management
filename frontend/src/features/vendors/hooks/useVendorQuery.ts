/**
 * Vendor Query Hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { vendorApi } from '../api/vendorApi'
import { VendorFilter, UpdateVendorRequest } from '../types/vendor.types'
import toast from 'react-hot-toast'

export function useVendors(filters?: VendorFilter) {
  return useQuery({
    queryKey: ['vendors', filters],
    queryFn: () => vendorApi.getAll(filters),
    staleTime: 2 * 60 * 1000,
  })
}

export function useVendor(id: number) {
  return useQuery({
    queryKey: ['vendors', id],
    queryFn: () => vendorApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateVendor() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: vendorApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors'] })
      toast.success('Vendor created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create vendor')
    }
  })
}

export function useUpdateVendor(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: UpdateVendorRequest) => vendorApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors', id] })
      queryClient.invalidateQueries({ queryKey: ['vendors'] })
      toast.success('Vendor updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update vendor')
    }
  })
}

export function useSuspendVendor(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => vendorApi.suspend(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors', id] })
      toast.success('Vendor suspended successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to suspend vendor')
    }
  })
}

export function useActivateVendor(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => vendorApi.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vendors', id] })
      toast.success('Vendor activated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to activate vendor')
    }
  })
}
