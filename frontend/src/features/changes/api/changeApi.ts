/**
 * Change Management API Service
 * Provides CRUD operations for change cases
 */
import api from '@/services/api'
import {
  ChangeCase,
  CreateChangeCaseRequest,
  UpdateChangeCaseRequest,
  ApproveChangeRequest,
  RejectChangeRequest,
  ImplementChangeRequest,
  CancelChangeRequest,
  ChangeCaseFilters,
  ChangeCaseListResponse,
  ChangeHistory,
  ChangeApproval
} from '../types/change.types'

export const changeApi = {
  /**
   * Get all change cases with optional filters
   */
  getAll: async (filters?: ChangeCaseFilters): Promise<ChangeCaseListResponse> => {
    const params = new URLSearchParams()
    if (filters?.charter_id) params.append('charter_id', filters.charter_id.toString())
    if (filters?.client_id) params.append('client_id', filters.client_id.toString())
    if (filters?.vendor_id) params.append('vendor_id', filters.vendor_id.toString())
    if (filters?.status) params.append('status', filters.status)
    if (filters?.change_type) params.append('change_type', filters.change_type)
    if (filters?.priority) params.append('priority', filters.priority)
    if (filters?.page) params.append('page', filters.page.toString())
    if (filters?.page_size) params.append('page_size', filters.page_size.toString())
    
    const response = await api.get<ChangeCaseListResponse>(`/api/v1/changes/cases?${params}`)
    return response.data
  },

  /**
   * Get a specific change case by ID
   */
  getById: async (id: number): Promise<ChangeCase> => {
    const response = await api.get<ChangeCase>(`/api/v1/changes/cases/${id}`)
    return response.data
  },

  /**
   * Get change cases for a specific charter
   */
  getByCharter: async (charterId: number): Promise<ChangeCaseListResponse> => {
    const response = await api.get<ChangeCaseListResponse>(
      `/api/v1/changes/cases?charter_id=${charterId}`
    )
    return response.data
  },

  /**
   * Create a new change case
   */
  create: async (data: CreateChangeCaseRequest): Promise<ChangeCase> => {
    const response = await api.post<ChangeCase>('/api/v1/changes/cases', data)
    return response.data
  },

  /**
   * Update an existing change case
   */
  update: async (id: number, data: UpdateChangeCaseRequest): Promise<ChangeCase> => {
    const params = new URLSearchParams()
    params.append('updated_by', '1') // TODO: Get from auth context
    params.append('updated_by_name', 'Admin User') // TODO: Get from auth context
    
    const response = await api.put<ChangeCase>(
      `/api/v1/changes/cases/${id}?${params}`,
      data
    )
    return response.data
  },

  /**
   * Move change case to review status
   */
  moveToReview: async (id: number): Promise<ChangeCase> => {
    const params = new URLSearchParams()
    params.append('reviewed_by', '1') // TODO: Get from auth context
    params.append('reviewed_by_name', 'Admin User') // TODO: Get from auth context
    
    const response = await api.post<ChangeCase>(
      `/api/v1/changes/cases/${id}/review?${params}`
    )
    return response.data
  },

  /**
   * Approve a change case
   */
  approve: async (id: number, data: ApproveChangeRequest): Promise<ChangeCase> => {
    const response = await api.post<ChangeCase>(
      `/api/v1/changes/cases/${id}/approve`,
      data
    )
    return response.data
  },

  /**
   * Reject a change case
   */
  reject: async (id: number, data: RejectChangeRequest): Promise<ChangeCase> => {
    const response = await api.post<ChangeCase>(
      `/api/v1/changes/cases/${id}/reject`,
      data
    )
    return response.data
  },

  /**
   * Mark change case as implemented
   */
  implement: async (id: number, data: ImplementChangeRequest): Promise<ChangeCase> => {
    const response = await api.post<ChangeCase>(
      `/api/v1/changes/cases/${id}/implement`,
      data
    )
    return response.data
  },

  /**
   * Cancel a change case
   */
  cancel: async (id: number, data: CancelChangeRequest): Promise<ChangeCase> => {
    const response = await api.post<ChangeCase>(
      `/api/v1/changes/cases/${id}/cancel`,
      data
    )
    return response.data
  },

  /**
   * Get complete audit history for a change case
   */
  getHistory: async (caseId: number): Promise<ChangeHistory[]> => {
    const response = await api.get<ChangeHistory[]>(
      `/api/v1/changes/cases/${caseId}/history`
    )
    return response.data
  },

  /**
   * Get approvals for a change case
   */
  getApprovals: async (caseId: number): Promise<ChangeApproval[]> => {
    const response = await api.get<ChangeApproval[]>(
      `/api/v1/changes/cases/${caseId}/approvals`
    )
    return response.data
  }
}
