import api from '@/services/api'
import { useAuthStore } from '@/store/authStore'
import { Lead, CreateLeadRequest, UpdateLeadRequest, LeadFilters } from '../types/lead.types'

const SALES_API_PREFIX = '/api/v1/sales/api/v1'

export const leadApi = {
  getAll: async (filters?: LeadFilters) => {
    const params = new URLSearchParams()
    if (filters?.status) params.append('status', filters.status)
    if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to.toString())
    if (filters?.date_from) params.append('created_after', filters.date_from)
    if (filters?.date_to) params.append('created_before', filters.date_to)
    
    const response = await api.get<Lead[]>(`${SALES_API_PREFIX}/leads?${params}`)
    return response.data
  },
  
  getById: async (id: number) => {
    const response = await api.get<Lead>(`${SALES_API_PREFIX}/leads/${id}`)
    return response.data
  },
  
  create: async (data: CreateLeadRequest) => {
    const response = await api.post<Lead>(`${SALES_API_PREFIX}/leads`, data)
    return response.data
  },
  
  update: async (id: number, data: UpdateLeadRequest) => {
    const response = await api.put<Lead>(`${SALES_API_PREFIX}/leads/${id}`, data)
    return response.data
  },
  
  delete: async (id: number) => {
    await api.delete(`${SALES_API_PREFIX}/leads/${id}`)
  },
  
  convertToQuote: async (id: number) => {
    const userId = useAuthStore.getState().user?.id
    const query = userId ? `?user_id=${userId}` : ''
    const response = await api.post<{ charter_id: number; client_id: number }>(
      `${SALES_API_PREFIX}/leads/${id}/convert${query}`
    )
    return response.data
  },
  
  assign: async (id: number, userId: number) => {
    const response = await api.post(`${SALES_API_PREFIX}/leads/${id}/assign`, { user_id: userId })
    return response.data
  }
}
