/**
 * QC Task Custom Hooks
 * Data fetching and mutation hooks using React Query
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { qcApi } from '../api/qcApi'
import { QCTaskFilters, UpdateQCTaskRequest } from '../types/qc.types'
import toast from 'react-hot-toast'

export function useQCTasks(filters?: QCTaskFilters) {
  return useQuery({
    queryKey: ['qcTasks', filters],
    queryFn: () => qcApi.getAll(filters),
    staleTime: 2 * 60 * 1000,
  })
}

export function useQCTask(id: number) {
  return useQuery({
    queryKey: ['qcTasks', id],
    queryFn: () => qcApi.getById(id),
    enabled: !!id,
  })
}

export function useCreateQCTask() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: qcApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qcTasks'] })
      toast.success('QC task created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create QC task')
    }
  })
}

export function useUpdateQCTask(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: UpdateQCTaskRequest) => qcApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qcTasks', id] })
      queryClient.invalidateQueries({ queryKey: ['qcTasks'] })
      toast.success('QC task updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update QC task')
    }
  })
}

export function useCompleteQCTask(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (notes?: string) => qcApi.complete(id, notes),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['qcTasks', id] })
      queryClient.invalidateQueries({ queryKey: ['qcTasks'] })
      toast.success('QC task completed successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to complete QC task')
    }
  })
}
