import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { leadApi } from '../api/leadApi'
import { CreateLeadRequest, UpdateLeadRequest, LeadFilters } from '../types/lead.types'
import toast from 'react-hot-toast'

// Query Keys
export const leadKeys = {
  all: ['leads'] as const,
  lists: () => [...leadKeys.all, 'list'] as const,
  list: (filters?: LeadFilters) => [...leadKeys.lists(), { filters }] as const,
  details: () => [...leadKeys.all, 'detail'] as const,
  detail: (id: number) => [...leadKeys.details(), id] as const,
}

// Query Hooks
export function useLeads(filters?: LeadFilters) {
  return useQuery({
    queryKey: leadKeys.list(filters),
    queryFn: () => leadApi.getAll(filters),
  })
}

export function useLead(id: number) {
  return useQuery({
    queryKey: leadKeys.detail(id),
    queryFn: () => leadApi.getById(id),
    enabled: !!id,
  })
}

// Mutation Hooks
export function useCreateLead() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CreateLeadRequest) => leadApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: leadKeys.lists() })
      toast.success('Lead created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create lead')
    },
  })
}

export function useUpdateLead() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: UpdateLeadRequest }) => 
      leadApi.update(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: leadKeys.lists() })
      queryClient.invalidateQueries({ queryKey: leadKeys.detail(variables.id) })
      toast.success('Lead updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update lead')
    },
  })
}

export function useDeleteLead() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => leadApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: leadKeys.lists() })
      toast.success('Lead deleted successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete lead')
    },
  })
}

export function useConvertLead() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (id: number) => leadApi.convertToQuote(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: leadKeys.lists() })
      toast.success('Lead converted to quote successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to convert lead')
    },
  })
}

export function useAssignLead() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ leadId, userId }: { leadId: number; userId: number }) => 
      leadApi.assign(leadId, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: leadKeys.lists() })
      toast.success('Lead assigned successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to assign lead')
    },
  })
}
