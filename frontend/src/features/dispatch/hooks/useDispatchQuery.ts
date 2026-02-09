/**
 * Dispatch Query Hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { dispatchApi } from '../api/dispatchApi'
import { DispatchFilters } from '../types/dispatch.types'
import toast from 'react-hot-toast'

export function useDispatchTrips(filters?: DispatchFilters) {
  return useQuery({
    queryKey: ['dispatch-trips', filters],
    queryFn: () => dispatchApi.getTrips(filters),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })
}

export function useDispatchDrivers() {
  return useQuery({
    queryKey: ['dispatch-drivers'],
    queryFn: () => dispatchApi.getDrivers(),
  })
}

export function useAssignDriver() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ tripId, driverId }: { tripId: number; driverId: number }) => 
      dispatchApi.assignDriver(tripId, driverId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-trips'] })
      toast.success('Driver assigned successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to assign driver')
    }
  })
}

export function useUnassignDriver() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (tripId: number) => dispatchApi.unassignDriver(tripId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-trips'] })
      toast.success('Driver unassigned successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to unassign driver')
    }
  })
}

export function useUpdateTripStatus() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ tripId, status }: { tripId: number; status: string }) => 
      dispatchApi.updateTripStatus(tripId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-trips'] })
      toast.success('Trip status updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update trip status')
    }
  })
}

export function useUpdatePriority() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ tripId, priority }: { tripId: number; priority: string }) => 
      dispatchApi.updatePriority(tripId, priority),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dispatch-trips'] })
      toast.success('Priority updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update priority')
    }
  })
}
