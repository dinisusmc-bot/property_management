import { useQuery } from '@tanstack/react-query'
import { dashboardApi } from '../api/dashboardApi'

// Query Keys
export const dashboardKeys = {
  all: ['dashboard'] as const,
  metrics: (period: string) => [...dashboardKeys.all, 'metrics', period] as const,
  funnel: (period: string) => [...dashboardKeys.all, 'funnel', period] as const,
  topPerformers: () => [...dashboardKeys.all, 'top-performers'] as const,
  activity: () => [...dashboardKeys.all, 'activity'] as const,
  stats: () => [...dashboardKeys.all, 'stats'] as const,
}

// Get sales metrics
export function useSalesMetrics(period: 'today' | 'week' | 'month' | 'quarter' = 'month') {
  return useQuery({
    queryKey: dashboardKeys.metrics(period),
    queryFn: () => dashboardApi.getSalesMetrics(period),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

// Get conversion funnel
export function useConversionFunnel(period: 'week' | 'month' | 'quarter' = 'month') {
  return useQuery({
    queryKey: dashboardKeys.funnel(period),
    queryFn: () => dashboardApi.getConversionFunnel(period),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Get top performers
export function useTopPerformers(limit: number = 10) {
  return useQuery({
    queryKey: dashboardKeys.topPerformers(),
    queryFn: () => dashboardApi.getTopPerformers(limit),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

// Get recent activity
export function useRecentActivity(limit: number = 10) {
  return useQuery({
    queryKey: dashboardKeys.activity(),
    queryFn: () => dashboardApi.getRecentActivity(limit),
    staleTime: 1 * 60 * 1000, // 1 minute
  })
}

// Get dashboard stats
export function useDashboardStats() {
  return useQuery({
    queryKey: dashboardKeys.stats(),
    queryFn: () => dashboardApi.getDashboardStats(),
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}
