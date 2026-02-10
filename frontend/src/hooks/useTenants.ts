import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../services/apiClient';

interface Tenant {
  id: number;
  full_name: string;
  email: string;
  phone: string;
  unit_id: number;
  is_primary: boolean;
  status: 'active' | 'inactive' | 'pending';
  created_at: string;
}

export const useTenants = () => {
  return useQuery({
    queryKey: ['tenants'],
    queryFn: async () => {
      const res = await apiClient.get<Tenant[]>('/tenants/tenants');
      return res.data;
    },
  });
};

export const useCreateTenant = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (newTenant: Omit<Tenant, 'id' | 'created_at'>) => {
      const res = await apiClient.post<Tenant>('/tenants/tenants', newTenant);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tenants'] });
    },
  });
};
