export interface SalesMetrics {
  period: string
  total_leads: number
  new_leads: number
  contacted: number
  qualified: number
  converted: number
  conversion_rate: number
  avg_response_time_hours: number
  active_agents: number
}

export interface ConversionFunnel {
  period: string
  funnel: Array<{
    stage: string
    count: number
    percentage: number
  }>
  conversion_rate: number
}

export interface TopPerformer {
  agent_id: number
  total_leads: number
  conversions: number
  conversion_rate: number
}

export interface TopPerformersResponse {
  period: string
  performers: TopPerformer[]
}

export interface RecentActivityItem {
  id: number
  lead_id: number
  activity_type: string
  type?: string
  subject?: string | null
  details: string
  performed_by: number
  created_at: string | null
}

export interface RecentActivityResponse {
  activities: RecentActivityItem[]
}

export interface DashboardStats {
  total_leads: number
  converted_leads: number
  active_leads: number
  recent_leads_30d: number
  overall_conversion_rate: number
}
