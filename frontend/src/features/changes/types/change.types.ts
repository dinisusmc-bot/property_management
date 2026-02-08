/**
 * Change Management TypeScript Types
 * Aligned with backend schemas.py
 */

export enum ChangeType {
  ITINERARY_MODIFICATION = 'itinerary_modification',
  PASSENGER_COUNT_CHANGE = 'passenger_count_change',
  VEHICLE_CHANGE = 'vehicle_change',
  DATE_TIME_CHANGE = 'date_time_change',
  PICKUP_LOCATION_CHANGE = 'pickup_location_change',
  DESTINATION_CHANGE = 'destination_change',
  AMENITY_ADDITION = 'amenity_addition',
  AMENITY_REMOVAL = 'amenity_removal',
  CANCELLATION = 'cancellation',
  PRICING_ADJUSTMENT = 'pricing_adjustment',
  OTHER = 'other'
}

export enum ChangeStatus {
  PENDING = 'pending',
  UNDER_REVIEW = 'under_review',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  IMPLEMENTED = 'implemented',
  CANCELLED = 'cancelled'
}

export enum ChangePriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

export enum ImpactLevel {
  MINIMAL = 'minimal',
  MODERATE = 'moderate',
  SIGNIFICANT = 'significant',
  MAJOR = 'major'
}

export enum ApprovalStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  CONDITIONAL = 'conditional'
}

export interface ChangeCase {
  id: number
  case_number: string
  charter_id: number
  client_id: number
  vendor_id: number | null
  change_type: ChangeType
  status: ChangeStatus
  priority: ChangePriority
  title: string
  description: string
  reason: string
  impact_level: ImpactLevel
  impact_assessment: string | null
  affects_vendor: boolean
  affects_pricing: boolean
  affects_schedule: boolean
  current_price: number | null
  proposed_price: number | null
  proposed_changes: Record<string, any> | null
  tags: string[] | null
  due_date: string | null
  requested_by: number
  requested_by_name: string
  reviewed_by: number | null
  reviewed_by_name: string | null
  approved_by: number | null
  approved_by_name: string | null
  implemented_by: number | null
  implemented_by_name: string | null
  rejection_reason: string | null
  cancellation_reason: string | null
  implementation_notes: string | null
  created_at: string
  updated_at: string | null
  reviewed_at: string | null
  approved_at: string | null
  rejected_at: string | null
  implemented_at: string | null
  cancelled_at: string | null
}

export interface CreateChangeCaseRequest {
  charter_id: number
  client_id: number
  vendor_id?: number | null
  change_type: ChangeType
  priority?: ChangePriority
  title: string
  description: string
  reason: string
  impact_level?: ImpactLevel
  impact_assessment?: string | null
  affects_vendor?: boolean
  affects_pricing?: boolean
  affects_schedule?: boolean
  current_price?: number | null
  proposed_price?: number | null
  proposed_changes?: Record<string, any> | null
  tags?: string[] | null
  due_date?: string | null
  requested_by: number
  requested_by_name: string
}

export interface UpdateChangeCaseRequest {
  priority?: ChangePriority
  title?: string
  description?: string
  reason?: string
  impact_level?: ImpactLevel
  impact_assessment?: string | null
  affects_vendor?: boolean
  affects_pricing?: boolean
  affects_schedule?: boolean
  proposed_price?: number | null
  proposed_changes?: Record<string, any> | null
  tags?: string[] | null
  due_date?: string | null
}

export interface ApproveChangeRequest {
  approved_by: number
  approved_by_name: string
  notes?: string
}

export interface RejectChangeRequest {
  rejected_by: number
  rejected_by_name: string
  reason: string
}

export interface ImplementChangeRequest {
  implemented_by: number
  implemented_by_name: string
  notes?: string
}

export interface CancelChangeRequest {
  cancelled_by: number
  cancelled_by_name: string
  reason: string
}

export interface ChangeCaseFilters {
  charter_id?: number
  client_id?: number
  vendor_id?: number
  status?: ChangeStatus
  change_type?: ChangeType
  priority?: ChangePriority
  page?: number
  page_size?: number
}

export interface ChangeCaseListResponse {
  items: ChangeCase[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface ChangeHistory {
  id: number
  case_id: number
  action: string
  changed_by: number
  changed_by_name: string
  old_values: Record<string, any> | null
  new_values: Record<string, any> | null
  notes: string | null
  ip_address: string | null
  user_agent: string | null
  created_at: string
}

export interface ChangeApproval {
  id: number
  case_id: number
  approver_role: string
  approver_id: number
  approver_name: string
  approver_email: string
  status: ApprovalStatus
  approved_at: string | null
  notes: string | null
  created_at: string
}
