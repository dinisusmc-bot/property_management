/**
 * Payment Mutation Hooks
 */
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { paymentApi } from '../api/paymentApi'
import toast from 'react-hot-toast'

export function useCreatePaymentOverride({ onSuccess }: { onSuccess?: () => void }) {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: paymentApi.createOverride,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payments'] })
      toast.success('Payment override applied successfully')
      onSuccess?.()
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to apply payment override')
    }
  })
}
