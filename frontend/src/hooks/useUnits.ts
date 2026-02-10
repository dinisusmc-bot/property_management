import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../services/apiClient';

interface Unit {
  id: number;
  unit_number: string;
  property_id: number;
  type: 'studio' | '1br' | '2br' | '3br' | 'commercial';
  rent: number;
  tenant_id?: number;
  status: 'vacant' | 'occupied' | 'maintenance';
  created_at: string;
}

export const useUnits = () => {
  return useQuery({
    queryKey: ['units'],
    queryFn: async () => {
      const res = await apiClient.get<Unit[]>('/units/units');
      return res.data;
    },
  });
};

export const useCreateUnit = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (newUnit: Omit<Unit, 'id' | 'created_at'>) => {
      const res = await apiClient.post<Unit>('/units/units', newUnit);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['units'] });
    },
  });
};
