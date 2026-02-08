/**
 * React Query Hooks for Change Management
 * Provides data fetching with caching and automatic refetching
 */
import { useQuery } from '@tanstack/react-query'
import { changeApi } from '../api/changeApi'
import { ChangeCaseFilters } from '../types/change.types'

/**
 * Fetch all change cases with optional filters
 */
export function useChangeCases(filters?: ChangeCaseFilters) {
  return useQuery({
    queryKey: ['changes', 'list', filters],
    queryFn: () => changeApi.getAll(filters),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

/**
 * Fetch a specific change case by ID
 */
export function useChangeCase(id: number) {
  return useQuery({
    queryKey: ['changes', 'detail', id],
    queryFn: () => changeApi.getById(id),
    enabled: !!id && id > 0,
    staleTime: 2 * 60 * 1000,
  })
}

/**
 * Fetch change cases for a specific charter
 */
export function useCharterChanges(charterId: number) {
  return useQuery({
    queryKey: ['changes', 'charter', charterId],
    queryFn: () => changeApi.getByCharter(charterId),
    enabled: !!charterId && charterId > 0,
    staleTime: 2 * 60 * 1000,
  })
}

/**
 * Fetch change case history
 */
export function useChangeCaseHistory(caseId: number) {
  return useQuery({
    queryKey: ['changes', 'history', caseId],
    queryFn: () => changeApi.getHistory(caseId),
    enabled: !!caseId && caseId > 0,
    staleTime: 5 * 60 * 1000, // 5 minutes - history doesn't change often
  })
}

/**
 * Fetch change case approvals
 */
export function useChangeCaseApprovals(caseId: number) {
  return useQuery({
    queryKey: ['changes', 'approvals', caseId],
    queryFn: () => changeApi.getApprovals(caseId),
    enabled: !!caseId && caseId > 0,
    staleTime: 2 * 60 * 1000,
  })
}
