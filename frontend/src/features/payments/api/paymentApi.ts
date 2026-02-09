/**
 * Payment API Service
 */
import api from '@/services/api'
import { PaymentOverrideFormData } from '../types/payment.types'

export const paymentApi = {
  createOverride: async (data: PaymentOverrideFormData) => {
    const response = await api.post('/api/v1/payments/override', data)
    return response.data
  },
  
  createManualPayment: async (data: PaymentOverrideFormData) => {
    const response = await api.post('/api/v1/payments/manual', data)
    return response.data
  }
}
