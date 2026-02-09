/**
 * QC Task TypeScript Types
 * Aligned with backend schemas
 */

export enum QCTaskType {
  COI_VERIFICATION = 'coi_verification',
  PAYMENT_VERIFICATION = 'payment_verification',
  ITINERARY_REVIEW = 'itinerary_review',
  DOCUMENT_CHECK = 'document_check',
  OTHER = 'other'
}

export enum QCTaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed'
}

export interface QCTask {
  id: number
  charter_id: number
  task_type: QCTaskType
  status: QCTaskStatus
  assigned_to: number | null
  assigned_to_name: string | null
  due_date: string
  completed_at: string | null
  notes: string | null
  charter_reference: string | null
  created_at: string
}

export interface QCTaskFilters {
  status?: QCTaskStatus
  task_type?: QCTaskType
  assigned_to?: number
  overdue?: boolean
}

export interface CreateQCTaskRequest {
  charter_id: number
  task_type: QCTaskType
  due_date: string
  assigned_to?: number
  notes?: string
}

export interface UpdateQCTaskRequest {
  status?: QCTaskStatus
  assigned_to?: number
  notes?: string
  completed_at?: string
}
