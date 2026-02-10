import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../services/apiClient';

interface Property {
  id: number;
  name: string;
  address: string;
  owner_id: number;
  status: 'active' | 'inactive';
  created_at: string;
}

export const useProperties = () => {
  return useQuery({
    queryKey: ['properties'],
    queryFn: async () => {
      const res = await apiClient.get<Property[]>('/properties/properties');
      return res.data;
    },
  });
};

export const useCreateProperty = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (newProperty: Omit<Property, 'id' | 'created_at'>) => {
      const res = await apiClient.post<Property>('/properties/properties', newProperty);
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['properties'] });
    },
  });
};
