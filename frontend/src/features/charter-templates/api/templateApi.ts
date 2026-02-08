import api from '@/services/api'
import {
  CharterTemplate,
  CloneCharterRequest,
  RecurringCharterRequest,
  CreateTemplateRequest,
  ApplyTemplateRequest,
} from '../types/template.types'

export const templateApi = {
  // Clone single charter
  cloneCharter: async (request: CloneCharterRequest) => {
    const { charter_id, ...payload } = request
    const response = await api.post(`/api/v1/charters/${charter_id}/clone`, payload)
    return response.data
  },

  // Create recurring charters
  createRecurringCharters: async (request: RecurringCharterRequest) => {
    const response = await api.post('/api/v1/charters/series', request)
    return response.data
  },

  // Get all templates
  getTemplates: async () => {
    const response = await api.get<CharterTemplate[]>('/api/v1/charters/templates')
    return response.data
  },

  // Get single template
  getTemplate: async (id: number) => {
    const response = await api.get<CharterTemplate>(`/api/v1/charters/templates/${id}`)
    return response.data
  },

  // Create template from charter
  createTemplate: async (request: CreateTemplateRequest) => {
    const response = await api.post<CharterTemplate>(
      `/api/v1/charters/${request.charter_id}/save-as-template`,
      { template_name: request.template_name }
    )
    return response.data
  },

  // Update template
  updateTemplate: async (id: number, data: Partial<CharterTemplate>) => {
    const response = await api.put<CharterTemplate>(`/api/v1/charters/templates/${id}`, data)
    return response.data
  },

  // Delete template
  deleteTemplate: async (id: number) => {
    await api.delete(`/api/v1/charters/templates/${id}`)
  },

  // Apply template to create new charter
  applyTemplate: async (request: ApplyTemplateRequest) => {
    const { template_id, ...payload } = request
    const response = await api.post(`/api/v1/charters/clone/${template_id}`, payload)
    return response.data
  },
}
