import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templateApi } from '../api/templateApi'
import {
  CloneCharterRequest,
  RecurringCharterRequest,
  CreateTemplateRequest,
  ApplyTemplateRequest,
} from '../types/template.types'
import toast from 'react-hot-toast'

// Query Keys
export const templateKeys = {
  all: ['templates'] as const,
  lists: () => [...templateKeys.all, 'list'] as const,
  detail: (id: number) => [...templateKeys.all, 'detail', id] as const,
}

// Get all templates
export function useTemplates() {
  return useQuery({
    queryKey: templateKeys.lists(),
    queryFn: () => templateApi.getTemplates(),
    staleTime: 5 * 60 * 1000,
  })
}

// Get single template
export function useTemplate(id: number) {
  return useQuery({
    queryKey: templateKeys.detail(id),
    queryFn: () => templateApi.getTemplate(id),
    enabled: !!id,
  })
}

// Clone charter
export function useCloneCharter() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: CloneCharterRequest) => templateApi.cloneCharter(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['charters'] })
      toast.success('Charter cloned successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to clone charter')
    },
  })
}

// Create recurring charters
export function useCreateRecurringCharters() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: RecurringCharterRequest) => templateApi.createRecurringCharters(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['charters'] })
      toast.success('Recurring series created successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create recurring charters')
    },
  })
}

// Create template
export function useCreateTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: CreateTemplateRequest) => templateApi.createTemplate(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() })
      toast.success('Template created successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create template')
    },
  })
}

// Update template
export function useUpdateTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) =>
      templateApi.updateTemplate(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() })
      queryClient.invalidateQueries({ queryKey: templateKeys.detail(variables.id) })
      toast.success('Template updated successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update template')
    },
  })
}

// Delete template
export function useDeleteTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => templateApi.deleteTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() })
      toast.success('Template deleted successfully!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to delete template')
    },
  })
}

// Apply template
export function useApplyTemplate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (request: ApplyTemplateRequest) => templateApi.applyTemplate(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['charters'] })
      toast.success('Charter created from template!')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to apply template')
    },
  })
}
