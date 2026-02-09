/**
 * Vendor Portal API Service
 */
import api from '@/services/api'
import { VendorAuthRequest, VendorAuthResponse, VendorProfile, VendorBid, VendorTrip } from '../types/vendor-portal.types'

export const vendorPortalApi = {
  login: async (credentials: VendorAuthRequest) => {
    const response = await api.post<VendorAuthResponse>('/api/v1/vendor-portal/login', credentials)
    return response.data
  },
  
  logout: async () => {
    const response = await api.post('/api/v1/vendor-portal/logout')
    return response.data
  },
  
  getProfile: async () => {
    const response = await api.get<VendorProfile>('/api/v1/vendor-portal/profile')
    return response.data
  },
  
  getBids: async () => {
    const response = await api.get<VendorBid[]>('/api/v1/vendor-portal/bids')
    return response.data
  },
  
  getTrips: async () => {
    const response = await api.get<VendorTrip[]>('/api/v1/vendor-portal/trips')
    return response.data
  },
  
  submitBid: async (charterId: number, amount: number) => {
    const response = await api.post<VendorBid>('/api/v1/vendor-portal/bids', {
      charter_id: charterId,
      amount: amount
    })
    return response.data
  },
  
  updateCOI: async (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    
    const response = await api.post('/api/v1/vendor-portal/coi', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    return response.data
  }
}
