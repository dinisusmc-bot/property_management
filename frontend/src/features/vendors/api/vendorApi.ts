/**
 * Vendor API Service
 */
import api from '@/services/api'
import { Vendor, VendorDetail, CreateVendorRequest, UpdateVendorRequest, VendorFilter } from '../types/vendor.types'

export const vendorApi = {
  getAll: async (filters?: VendorFilter) => {
    const params = new URLSearchParams()
    if (filters?.name) params.append('name', filters.name)
    if (filters?.email) params.append('email', filters.email)
    if (filters?.status) params.append('status', filters.status)
    if (filters?.company_name) params.append('company_name', filters.company_name)
    
    const response = await api.get<Vendor[]>(`/api/v1/vendors?${params}`)
    return response.data
  },
  
  getById: async (id: number) => {
    const response = await api.get<VendorDetail>(`/api/v1/vendors/${id}`)
    return response.data
  },
  
  create: async (data: CreateVendorRequest) => {
    const response = await api.post<Vendor>('/api/v1/vendors', data)
    return response.data
  },
  
  update: async (id: number, data: UpdateVendorRequest) => {
    const response = await api.patch<Vendor>(`/api/v1/vendors/${id}`, data)
    return response.data
  },
  
  suspend: async (id: number) => {
    const response = await api.post<Vendor>(`/api/v1/vendors/${id}/suspend`)
    return response.data
  },
  
  activate: async (id: number) => {
    const response = await api.post<Vendor>(`/api/v1/vendors/${id}/activate`)
    return response.data
  },
  
  getCOIStatus: async (vendorId: number) => {
    const response = await api.get(`/api/v1/vendors/${vendorId}/coi`)
    return response.data
  },
  
  submitBidding: async (vendorId: number, charterId: number, amount: number) => {
    const response = await api.post(`/api/v1/bids`, { vendor_id: vendorId, charter_id: charterId, amount })
    return response.data
  }
}
