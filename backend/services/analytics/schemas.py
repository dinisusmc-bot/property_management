from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, Dict
from decimal import Decimal

# Revenue Analytics Schemas

class RevenueSummary(BaseModel):
    """Revenue summary response"""
    period: Dict[str, date]
    total_bookings: int
    total_revenue: float
    average_booking_value: float
    completed_revenue: float

class MonthlyRevenue(BaseModel):
    """Monthly revenue data"""
    month: int
    bookings: int
    revenue: float

class RevenueByMonth(BaseModel):
    """Revenue by month response"""
    year: int
    monthly_data: List[MonthlyRevenue]

class ClientRevenue(BaseModel):
    """Client revenue data"""
    client_id: int
    client_name: str
    total_bookings: int
    total_revenue: float

class RevenueByClient(BaseModel):
    """Revenue by client response"""
    period: Dict[str, date]
    top_clients: List[ClientRevenue]

# Charter Metrics Schemas

class StatusBreakdown(BaseModel):
    """Status breakdown response"""
    period: Dict[str, date]
    total_charters: int
    status_breakdown: Dict[str, int]
    completion_rate: float

class VehicleUtilization(BaseModel):
    """Vehicle utilization metrics"""
    vehicle_id: int
    vehicle_type: str
    total_charters: int
    total_hours: float
    utilization_rate: float

# Vendor Analytics Schemas

class VendorPerformance(BaseModel):
    """Vendor performance metrics"""
    vendor_id: int
    vendor_name: str
    total_charters: int
    average_rating: float
    on_time_percentage: float
    total_revenue: float

class VendorMetrics(BaseModel):
    """Vendor metrics response"""
    period: Dict[str, date]
    vendors: List[VendorPerformance]

# Dashboard Schemas

class MonthToDate(BaseModel):
    """Month-to-date metrics"""
    bookings: int
    revenue: float

class TodayMetrics(BaseModel):
    """Today's metrics"""
    active_charters: int

class DashboardData(BaseModel):
    """Dashboard aggregate data"""
    month_to_date: MonthToDate
    today: TodayMetrics
    pending_quotes: int
    timestamp: datetime

class DashboardSummary(BaseModel):
    """Complete dashboard summary"""
    revenue_summary: Dict
    charter_metrics: Dict
    vendor_summary: Dict
    recent_activity: List[Dict]
