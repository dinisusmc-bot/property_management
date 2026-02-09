/**
 * Client Query Hooks
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { clientApi } from '../api/clientApi'
import { ClientFilter, UpdateClientRequest } from '../types/client.types'
import toast from 'react-hot-toast'

export function useClients(filters?: ClientFilter) {
  return useQuery({
    queryKey: ['clients', filters],
    queryFn: () => clientApi.getAll(filters),
    staleTime: 2 * 60 * 1000,
  })
}

export function useClient(id: number) {
  return useQuery({
    queryKey: ['clients', id],
    queryFn: () => clientApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateClient() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: clientApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      toast.success('Client created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create client')
    }
  })
}

export function useUpdateClient(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: UpdateClientRequest) => clientApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients', id] })
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      toast.success('Client updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update client')
    }
  })
}

export function useSuspendClient(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => clientApi.suspend(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients', id] })
      toast.success('Client suspended successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to suspend client')
    }
  })
}

export function useActivateClient(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => clientApi.activate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients', id] })
      toast.success('Client activated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to activate client')
    }
  })
}
