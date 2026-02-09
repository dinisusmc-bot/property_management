/**
 * Client API Service
 */
import api from '@/services/api'
import { Client, ClientDetail, CreateClientRequest, UpdateClientRequest, ClientFilter } from '../types/client.types'

export const clientApi = {
  getAll: async (filters?: ClientFilter) => {
    const params = new URLSearchParams()
    if (filters?.name) params.append('name', filters.name)
    if (filters?.email) params.append('email', filters.email)
    if (filters?.status) params.append('status', filters.status)
    if (filters?.company_name) params.append('company_name', filters.company_name)
    
    const response = await api.get<Client[]>(`/api/v1/clients?${params}`)
    return response.data
  },
  
  getById: async (id: number) => {
    const response = await api.get<ClientDetail>(`/api/v1/clients/${id}`)
    return response.data
  },
  
  create: async (data: CreateClientRequest) => {
    const response = await api.post<Client>('/api/v1/clients', data)
    return response.data
  },
  
  update: async (id: number, data: UpdateClientRequest) => {
    const response = await api.patch<Client>(`/api/v1/clients/${id}`, data)
    return response.data
  },
  
  suspend: async (id: number) => {
    const response = await api.post<Client>(`/api/v1/clients/${id}/suspend`)
    return response.data
  },
  
  activate: async (id: number) => {
    const response = await api.post<Client>(`/api/v1/clients/${id}/activate`)
    return response.data
  },
  
  getTripHistory: async (clientId: number) => {
    const response = await api.get(`/api/v1/charters?client_id=${clientId}`)
    return response.data
  },
  
  getPayments: async (clientId: number) => {
    const response = await api.get(`/api/v1/payments?client_id=${clientId}`)
    return response.data
  },
  
  getDocuments: async (clientId: number) => {
    const response = await api.get(`/api/v1/documents?client_id=${clientId}`)
    return response.data
  }
}
