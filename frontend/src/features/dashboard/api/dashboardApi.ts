import api from '@/services/api'
import {
  SalesMetrics,
  ConversionFunnel,
  TopPerformersResponse,
  RecentActivityResponse,
  DashboardStats,
} from '../types/dashboard.types'

export const dashboardApi = {
  // Sales service endpoints include /api/v1 internally
  basePath: '/api/v1/sales/api/v1/sales',
  // Get sales metrics for current agent
  getSalesMetrics: async (period: 'today' | 'week' | 'month' | 'quarter' = 'month') => {
    const response = await api.get<SalesMetrics>(`${dashboardApi.basePath}/metrics?period=${period}`)
    return response.data
  },

  // Get conversion funnel data
  getConversionFunnel: async (period: 'week' | 'month' | 'quarter' = 'month') => {
    const response = await api.get<ConversionFunnel>(`${dashboardApi.basePath}/funnel?period=${period}`)
    return response.data
  },

  // Get top performers leaderboard
  getTopPerformers: async (limit: number = 10) => {
    const response = await api.get<TopPerformersResponse>(`${dashboardApi.basePath}/top-performers?limit=${limit}`)
    return response.data
  },

  // Get recent activity feed
  getRecentActivity: async (limit: number = 10) => {
    const response = await api.get<RecentActivityResponse>(`${dashboardApi.basePath}/activity?limit=${limit}`)
    return response.data
  },

  // Get dashboard stats summary
  getDashboardStats: async () => {
    const response = await api.get<DashboardStats>(`${dashboardApi.basePath}/stats`)
    return response.data
  },
}
