import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../services/apiClient';
import { OwnerResponse, OwnerCreate, OwnerUpdate } from '../pages/OwnersPage';

interface OwnerResponse {
  id: number;
  email: string;
  full_name: string;
  phone?: string;
  company_name?: string;
  address?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export const useOwners = () => {
  return useQuery({
    queryKey: ['owners'],
    queryFn: async () => {
      const res = await apiClient.get<OwnerResponse[]>('/owners/owners');
      return res.data;
    },
  });
};

export const useCreateOwner = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (newOwner: OwnerCreate) => {
      const res = await apiClient.post<OwnerResponse>('/owners/owners', newOwner);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['owners'] });
    },
  });
};

export const useUpdateOwner = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, data }: { id: number; data: OwnerUpdate }) => {
      const res = await apiClient.put<OwnerResponse>(`/owners/owners/${id}`, data);
      return res.data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['owners'] });
      queryClient.invalidateQueries({ queryKey: ['owners', variables.id] });
    },
  });
};
