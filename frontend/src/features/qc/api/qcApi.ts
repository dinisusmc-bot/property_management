/**
 * QC Task API Service
 * Provides typed API calls for QC task operations
 */
import api from '@/services/api'
import {
  QCTask,
  CreateQCTaskRequest,
  UpdateQCTaskRequest,
  QCTaskFilters
} from '../types/qc.types'

export const qcApi = {
  getAll: async (filters?: QCTaskFilters) => {
    const params = new URLSearchParams()
    if (filters?.status) params.append('status', filters.status)
    if (filters?.task_type) params.append('task_type', filters.task_type)
    if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to.toString())
    if (filters?.overdue) params.append('overdue', filters.overdue.toString())
    
    const response = await api.get<QCTask[]>(`/api/v1/qc/tasks?${params}`)
    return response.data
  },
  
  getById: async (id: number) => {
    const response = await api.get<QCTask>(`/api/v1/qc/tasks/${id}`)
    return response.data
  },
  
  create: async (data: CreateQCTaskRequest) => {
    const response = await api.post<QCTask>('/api/v1/qc/tasks', data)
    return response.data
  },
  
  update: async (id: number, data: UpdateQCTaskRequest) => {
    const response = await api.patch<QCTask>(`/api/v1/qc/tasks/${id}`, data)
    return response.data
  },
  
  complete: async (id: number, notes?: string) => {
    const response = await api.post<QCTask>(`/api/v1/qc/tasks/${id}/complete`, { notes })
    return response.data
  },
  
  assign: async (id: number, userId: number) => {
    const response = await api.post<QCTask>(`/api/v1/qc/tasks/${id}/assign`, { user_id: userId })
    return response.data
  }
}
