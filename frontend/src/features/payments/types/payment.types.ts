/**
 * Payment Types
 */
export interface PaymentOverrideFormData {
  charter_id: number
  payment_type: 'check' | 'wire' | 'cash' | 'other'
  amount: number
  payment_date: string
  reference_number?: string
  notes?: string
}
