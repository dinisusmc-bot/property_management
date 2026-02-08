/**
 * React Query Mutation Hooks for Change Management
 * Provides functions for creating, updating, and transitioning change cases
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { changeApi } from '../api/changeApi'
import {
  CreateChangeCaseRequest,
  UpdateChangeCaseRequest,
  ApproveChangeRequest,
  RejectChangeRequest,
  ImplementChangeRequest,
  CancelChangeRequest
} from '../types/change.types'

/**
 * Create a new change case
 */
export function useCreateChangeCase() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  
  return useMutation({
    mutationFn: (data: CreateChangeCaseRequest) => changeApi.create(data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['changes'] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'charter', data.charter_id] })
      toast.success('Change case created successfully')
      navigate(`/changes/${data.id}`)
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to create change case'
      toast.error(message)
    }
  })
}

/**
 * Update an existing change case
 */
export function useUpdateChangeCase(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: UpdateChangeCaseRequest) => changeApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', 'detail', id] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'list'] })
      toast.success('Change case updated successfully')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to update change case'
      toast.error(message)
    }
  })
}

/**
 * Move change case to review
 */
export function useMoveToReview(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: () => changeApi.moveToReview(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', 'detail', id] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'list'] })
      toast.success('Change case moved to review')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to move to review'
      toast.error(message)
    }
  })
}

/**
 * Approve a change case
 */
export function useApproveChangeCase(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: ApproveChangeRequest) => changeApi.approve(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', 'detail', id] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'list'] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'history', id] })
      toast.success('Change case approved')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to approve change case'
      toast.error(message)
    }
  })
}

/**
 * Reject a change case
 */
export function useRejectChangeCase(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: RejectChangeRequest) => changeApi.reject(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', 'detail', id] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'list'] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'history', id] })
      toast.success('Change case rejected')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to reject change case'
      toast.error(message)
    }
  })
}

/**
 * Mark change case as implemented
 */
export function useImplementChangeCase(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: ImplementChangeRequest) => changeApi.implement(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', 'detail', id] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'list'] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'history', id] })
      toast.success('Change case marked as implemented')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to implement change case'
      toast.error(message)
    }
  })
}

/**
 * Cancel a change case
 */
export function useCancelChangeCase(id: number) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: (data: CancelChangeRequest) => changeApi.cancel(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['changes', 'detail', id] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'list'] })
      queryClient.invalidateQueries({ queryKey: ['changes', 'history', id] })
      toast.success('Change case cancelled')
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || 'Failed to cancel change case'
      toast.error(message)
    }
  })
}
