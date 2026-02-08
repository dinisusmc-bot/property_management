from fastapi import FastAPI, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, datetime, timedelta
from typing import Optional, List
import logging

from database import get_db
from auth import get_current_user
from config import settings
from schemas import (
    RevenueSummary, RevenueByMonth, RevenueByClient,
    StatusBreakdown, VehicleUtilization,
    VendorPerformance, VendorMetrics,
    DashboardData, MonthToDate, TodayMetrics
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Analytics Service",
    description="Business intelligence and analytics for Athena Charter Management",
    version=settings.VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "version": settings.VERSION
    }

# ============================================================================
# REVENUE ANALYTICS
# ============================================================================

@app.get("/revenue/summary", response_model=RevenueSummary)
async def get_revenue_summary(
    start_date: date = Query(..., description="Start date for analysis"),
    end_date: date = Query(..., description="End date for analysis"),
    db: Session = Depends(get_db)
):
    """
    Get revenue summary for date range
    
    Returns:
    - Total bookings
    - Total revenue
    - Average booking value
    - Completed revenue only
    """
    logger.info(f"Getting revenue summary from {start_date} to {end_date}")
    
    result = db.execute(
        text("""
            SELECT 
                COUNT(*) as total_bookings,
                COALESCE(SUM(total_cost), 0) as total_revenue,
                COALESCE(AVG(total_cost), 0) as average_booking_value,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN total_cost ELSE 0 END), 0) as completed_revenue
            FROM public.charters
            WHERE trip_date BETWEEN :start_date AND :end_date
        """),
        {"start_date": start_date, "end_date": end_date}
    )
    
    row = result.first()
    
    return {
        "period": {"start": start_date, "end": end_date},
        "total_bookings": row[0] or 0,
        "total_revenue": float(row[1]) if row[1] else 0.0,
        "average_booking_value": float(row[2]) if row[2] else 0.0,
        "completed_revenue": float(row[3]) if row[3] else 0.0
    }

@app.get("/revenue/by-month", response_model=RevenueByMonth)
async def get_revenue_by_month(
    year: int = Query(..., description="Year for analysis"),
    db: Session = Depends(get_db)
):
    """
    Get monthly revenue breakdown for a year
    
    Returns monthly totals for bookings and revenue
    """
    logger.info(f"Getting monthly revenue for year {year}")
    
    result = db.execute(
        text("""
            SELECT 
                EXTRACT(MONTH FROM trip_date)::INTEGER as month,
                COUNT(*) as bookings,
                COALESCE(SUM(total_cost), 0) as revenue
            FROM public.charters
            WHERE EXTRACT(YEAR FROM trip_date) = :year
            GROUP BY EXTRACT(MONTH FROM trip_date)
            ORDER BY month
        """),
        {"year": year}
    )
    
    months = []
    for row in result.all():
        months.append({
            "month": int(row[0]),
            "bookings": row[1],
            "revenue": float(row[2]) if row[2] else 0.0
        })
    
    return {
        "year": year,
        "monthly_data": months
    }

@app.get("/revenue/by-client", response_model=RevenueByClient)
async def get_revenue_by_client(
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(10, description="Number of top clients to return"),
    db: Session = Depends(get_db)
):
    """
    Get top clients by revenue
    
    Returns clients ranked by total revenue in period
    """
    logger.info(f"Getting top {limit} clients by revenue")
    
    result = db.execute(
        text("""
            SELECT 
                c.client_id,
                COALESCE(cl.name, 'Unknown') as client_name,
                COUNT(*) as total_bookings,
                COALESCE(SUM(c.total_cost), 0) as total_revenue
            FROM public.charters c
            LEFT JOIN public.clients cl ON c.client_id = cl.id
            WHERE c.trip_date BETWEEN :start_date AND :end_date
            GROUP BY c.client_id, cl.name
            ORDER BY total_revenue DESC
            LIMIT :limit
        """),
        {"start_date": start_date, "end_date": end_date, "limit": limit}
    )
    
    clients = []
    for row in result.all():
        clients.append({
            "client_id": row[0],
            "client_name": row[1],
            "total_bookings": row[2],
            "total_revenue": float(row[3]) if row[3] else 0.0
        })
    
    return {
        "period": {"start": start_date, "end": end_date},
        "top_clients": clients
    }

# ============================================================================
# CHARTER METRICS
# ============================================================================

@app.get("/charters/completion-rate", response_model=StatusBreakdown)
async def get_completion_rate(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """
    Get charter completion rate and status breakdown
    
    Returns:
    - Total charters
    - Status breakdown
    - Completion rate percentage
    """
    logger.info(f"Getting completion rate from {start_date} to {end_date}")
    
    result = db.execute(
        text("""
            SELECT 
                status,
                COUNT(*) as count
            FROM public.charters
            WHERE trip_date BETWEEN :start_date AND :end_date
            GROUP BY status
        """),
        {"start_date": start_date, "end_date": end_date}
    )
    
    status_counts = {}
    total = 0
    
    for row in result.all():
        status_counts[row[0]] = row[1]
        total += row[1]
    
    completion_rate = (status_counts.get('completed', 0) / total * 100) if total > 0 else 0
    
    return {
        "period": {"start": start_date, "end": end_date},
        "total_charters": total,
        "status_breakdown": status_counts,
        "completion_rate": round(completion_rate, 2)
    }

@app.get("/charters/by-status")
async def get_charters_by_status(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """Get charter counts by status"""
    logger.info(f"Getting charters by status")
    
    result = db.execute(
        text("""
            SELECT 
                status,
                COUNT(*) as count,
                COALESCE(SUM(total_cost), 0) as revenue
            FROM public.charters
            WHERE trip_date BETWEEN :start_date AND :end_date
            GROUP BY status
            ORDER BY count DESC
        """),
        {"start_date": start_date, "end_date": end_date}
    )
    
    statuses = []
    for row in result.all():
        statuses.append({
            "status": row[0],
            "count": row[1],
            "revenue": float(row[2]) if row[2] else 0.0
        })
    
    return {
        "period": {"start": start_date, "end": end_date},
        "statuses": statuses
    }

@app.get("/charters/vehicle-utilization")
async def get_vehicle_utilization(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: Session = Depends(get_db)
):
    """
    Get vehicle utilization metrics
    
    Returns charters per vehicle and estimated hours used
    """
    logger.info(f"Getting vehicle utilization")
    
    result = db.execute(
        text("""
            SELECT 
                c.vehicle_id,
                COALESCE(v.name, 'Unknown') as vehicle_name,
                COUNT(*) as total_charters,
                COALESCE(SUM(c.trip_hours), 0) as total_hours
            FROM public.charters c
            LEFT JOIN public.vehicles v ON c.vehicle_id = v.id
            WHERE c.trip_date BETWEEN :start_date AND :end_date
                AND c.vehicle_id IS NOT NULL
            GROUP BY c.vehicle_id, v.name
            ORDER BY total_charters DESC
        """),
        {"start_date": start_date, "end_date": end_date}
    )
    
    vehicles = []
    for row in result.all():
        vehicles.append({
            "vehicle_id": row[0],
            "vehicle_name": row[1],
            "total_charters": row[2],
            "total_hours": round(float(row[3]), 2) if row[3] else 0.0
        })
    
    return {
        "period": {"start": start_date, "end": end_date},
        "vehicles": vehicles
    }

# ============================================================================
# VENDOR ANALYTICS
# ============================================================================

@app.get("/vendors/performance", response_model=VendorMetrics)
async def get_vendor_performance(
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """
    Get vendor performance metrics
    
    Returns:
    - Total charters per vendor
    - Average rating
    - On-time percentage
    - Total revenue generated
    """
    logger.info(f"Getting vendor performance metrics")
    
    result = db.execute(
        text("""
            SELECT 
                c.vendor_id,
                'Vendor ' || c.vendor_id as vendor_name,
                COUNT(c.id) as total_charters,
                0.0 as average_rating,
                COALESCE(SUM(c.total_cost), 0) as total_revenue
            FROM public.charters c
            WHERE c.trip_date BETWEEN :start_date AND :end_date
                AND c.vendor_id IS NOT NULL
            GROUP BY c.vendor_id
            ORDER BY total_charters DESC
            LIMIT :limit
        """),
        {"start_date": start_date, "end_date": end_date, "limit": limit}
    )
    
    vendors = []
    for row in result.all():
        vendors.append({
            "vendor_id": row[0],
            "vendor_name": row[1],
            "total_charters": row[2],
            "average_rating": round(float(row[3]), 2) if row[3] else 0.0,
            "on_time_percentage": 95.0,  # Placeholder - would need dispatch data
            "total_revenue": float(row[4]) if row[4] else 0.0
        })
    
    return {
        "period": {"start": start_date, "end": end_date},
        "vendors": vendors
    }

# ============================================================================
# DASHBOARD API
# ============================================================================

@app.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    db: Session = Depends(get_db)
):
    """
    Get aggregated dashboard data in one call
    
    Returns:
    - Month-to-date revenue and bookings
    - Today's active charters
    - Pending quotes count
    """
    logger.info("Getting dashboard data")
    
    today = date.today()
    start_of_month = today.replace(day=1)
    
    # Revenue this month
    revenue_result = db.execute(
        text("""
            SELECT 
                COUNT(*),
                COALESCE(SUM(total_cost), 0)
            FROM public.charters
            WHERE trip_date >= :start_date
        """),
        {"start_date": start_of_month}
    )
    rev_row = revenue_result.first()
    
    # Active charters today
    active_result = db.execute(
        text("""
            SELECT COUNT(*)
            FROM public.charters
            WHERE trip_date = :today 
                AND status IN ('confirmed', 'in_progress')
        """),
        {"today": today}
    )
    active_count = active_result.scalar()
    
    # Pending quotes
    quotes_result = db.execute(
        text("""
            SELECT COUNT(*)
            FROM public.charters
            WHERE status = 'pending'
        """)
    )
    pending_quotes = quotes_result.scalar()
    
    return {
        "month_to_date": {
            "bookings": rev_row[0] or 0,
            "revenue": float(rev_row[1]) if rev_row[1] else 0.0
        },
        "today": {
            "active_charters": active_count or 0
        },
        "pending_quotes": pending_quotes or 0,
        "timestamp": datetime.utcnow()
    }

@app.get("/dashboard/summary")
async def get_dashboard_summary(
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard summary with multiple metrics
    """
    logger.info("Getting comprehensive dashboard summary")
    
    today = date.today()
    start_of_month = today.replace(day=1)
    thirty_days_ago = today - timedelta(days=30)
    
    # Revenue metrics
    revenue_result = db.execute(
        text("""
            SELECT 
                COUNT(*) as total_bookings,
                COALESCE(SUM(total_cost), 0) as total_revenue,
                COALESCE(AVG(total_cost), 0) as avg_booking_value
            FROM public.charters
            WHERE trip_date >= :start_date
        """),
        {"start_date": start_of_month}
    )
    revenue_data = revenue_result.first()
    
    # Status breakdown
    status_result = db.execute(
        text("""
            SELECT 
                status,
                COUNT(*) as count
            FROM public.charters
            WHERE trip_date >= :start_date
            GROUP BY status
        """),
        {"start_date": thirty_days_ago}
    )
    status_breakdown = {row[0]: row[1] for row in status_result.all()}
    
    # Vendor summary
    vendor_result = db.execute(
        text("""
            SELECT 
                COUNT(DISTINCT vendor_id) as total_vendors,
                COUNT(*) as total_charters
            FROM public.charters
            WHERE trip_date >= :start_date
                AND vendor_id IS NOT NULL
        """),
        {"start_date": start_of_month}
    )
    vendor_data = vendor_result.first()
    
    return {
        "revenue_summary": {
            "month_to_date_bookings": revenue_data[0] or 0,
            "month_to_date_revenue": float(revenue_data[1]) if revenue_data[1] else 0.0,
            "average_booking_value": float(revenue_data[2]) if revenue_data[2] else 0.0
        },
        "charter_metrics": {
            "status_breakdown": status_breakdown,
            "total_active": sum(status_breakdown.values())
        },
        "vendor_summary": {
            "active_vendors": vendor_data[0] or 0,
            "total_charters": vendor_data[1] or 0
        },
        "timestamp": datetime.utcnow()
    }

# ============================================================================
# PROFIT ANALYTICS
# ============================================================================

@app.get("/profit/by-agent")
async def get_profit_by_agent(
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    db: Session = Depends(get_db)
):
    """
    Profit breakdown by client
    
    Returns profit, revenue, and margin grouped by client
    Note: Charters table doesn't have agent/user tracking, so this groups by client
    """
    logger.info(f"Getting profit by client from {start_date} to {end_date}")
    
    # Build WHERE clause conditionally
    date_filter = ""
    if start_date:
        date_filter += f" AND c.trip_date >= '{start_date.isoformat()}'"
    if end_date:
        date_filter += f" AND c.trip_date <= '{end_date.isoformat()}'"
    
    query = text(f"""
        SELECT 
            c.client_id,
            COUNT(c.id) as total_charters,
            COALESCE(SUM(c.total_cost), 0) as total_revenue,
            COALESCE(SUM(c.actual_cost), 0) as total_actual_cost,
            COALESCE(SUM(c.total_cost - c.actual_cost), 0) as total_profit,
            CASE 
                WHEN SUM(c.total_cost) > 0 
                THEN (SUM(c.total_cost - c.actual_cost) / SUM(c.total_cost) * 100)
                ELSE 0 
            END as avg_margin
        FROM charters c
        WHERE c.status IN ('completed', 'confirmed', 'approved')
            {date_filter}
        GROUP BY c.client_id
        ORDER BY total_profit DESC
    """)
    
    result = db.execute(query)
    rows = result.fetchall()
    
    clients = []
    for row in rows:
        clients.append({
            "client_id": row[0],
            "total_charters": row[1],
            "total_revenue": float(row[2]),
            "total_cost": float(row[3]),
            "profit": float(row[4]),
            "avg_profit_margin": float(row[5])
        })
    
    return {
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "by_client": clients,
        "summary": {
            "total_clients": len(clients),
            "total_profit": sum(c["profit"] for c in clients),
            "total_revenue": sum(c["total_revenue"] for c in clients)
        }
    }

@app.get("/profit/by-month")
async def get_profit_by_month(
    year: int = Query(..., description="Year for analysis"),
    db: Session = Depends(get_db)
):
    """
    Monthly profit breakdown for a year
    
    Returns revenue, cost, profit, and margin for each month
    """
    logger.info(f"Getting profit by month for year {year}")
    
    query = text("""
        SELECT 
            EXTRACT(MONTH FROM trip_date)::INTEGER as month,
            TO_CHAR(trip_date, 'Month') as month_name,
            COUNT(*) as charter_count,
            COALESCE(SUM(total_cost), 0) as total_revenue,
            COALESCE(SUM(actual_cost), 0) as total_cost,
            COALESCE(SUM(total_cost - actual_cost), 0) as profit,
            CASE 
                WHEN SUM(total_cost) > 0 
                THEN (SUM(total_cost - actual_cost) / SUM(total_cost) * 100)
                ELSE 0 
            END as profit_margin
        FROM charters
        WHERE EXTRACT(YEAR FROM trip_date) = :year
            AND status IN ('completed', 'confirmed', 'approved')
        GROUP BY EXTRACT(MONTH FROM trip_date), TO_CHAR(trip_date, 'Month')
        ORDER BY month
    """)
    
    result = db.execute(query, {"year": year})
    rows = result.fetchall()
    
    months = []
    for row in rows:
        months.append({
            "month": row[0],
            "month_name": row[1].strip(),
            "charter_count": row[2],
            "revenue": float(row[3]),
            "cost": float(row[4]),
            "profit": float(row[5]),
            "profit_margin": float(row[6])
        })
    
    return {
        "year": year,
        "months": months,
        "summary": {
            "total_charters": sum(m["charter_count"] for m in months),
            "total_revenue": sum(m["revenue"] for m in months),
            "total_cost": sum(m["cost"] for m in months),
            "total_profit": sum(m["profit"] for m in months),
            "avg_margin": (sum(m["profit"] for m in months) / sum(m["revenue"] for m in months) * 100) if sum(m["revenue"] for m in months) > 0 else 0
        }
    }


# ============================================================================
# PHASE 4: AGENT PERFORMANCE REPORTS (Task 4.1)
# ============================================================================

@app.get("/reports/agent-performance")
async def get_agent_performance_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    agent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Comprehensive agent performance report
    
    Metrics:
    - Total charters (completed, cancelled)
    - Revenue generated
    - Average charter value
    - Lead conversion rate
    - Follow-up completion rate
    """
    # Base query - uses materialized view for performance
    query = """
        SELECT 
            agent_id,
            agent_name,
            total_charters,
            completed_charters,
            cancelled_charters,
            total_revenue,
            avg_charter_value,
            total_leads,
            converted_leads,
            conversion_rate,
            total_follow_ups,
            completed_follow_ups,
            last_updated
        FROM analytics.agent_performance_summary
        WHERE 1=1
    """
    
    params = {}
    
    if agent_id:
        query += " AND agent_id = :agent_id"
        params['agent_id'] = agent_id
    
    # Note: Date filtering not implemented in materialized view
    # Would require refreshing view or querying base tables
    
    result = db.execute(text(query), params)
    agents = result.fetchall()
    
    return {
        "period": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "agents": [
            {
                "agent_id": row.agent_id,
                "agent_name": row.agent_name,
                "charters": {
                    "total": row.total_charters,
                    "completed": row.completed_charters,
                    "cancelled": row.cancelled_charters,
                    "revenue": float(row.total_revenue),
                    "avg_value": float(row.avg_charter_value)
                },
                "leads": {
                    "total": row.total_leads,
                    "converted": row.converted_leads,
                    "conversion_rate": float(row.conversion_rate)
                },
                "follow_ups": {
                    "total": row.total_follow_ups,
                    "completed": row.completed_follow_ups,
                    "completion_rate": (row.completed_follow_ups / row.total_follow_ups * 100) if row.total_follow_ups > 0 else 0
                }
            }
            for row in agents
        ],
        "last_updated": agents[0].last_updated.isoformat() if agents else None
    }


@app.get("/reports/team-comparison")
async def get_team_comparison(
    metric: str = Query("revenue", regex="^(revenue|charters|conversion_rate)$"),
    period: str = Query("month", regex="^(week|month|quarter|year)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Compare agents by key metrics
    
    Available metrics:
    - revenue: Total revenue generated
    - charters: Number of completed charters
    - conversion_rate: Lead to charter conversion percentage
    """
    # Use materialized view for faster queries
    if metric == "revenue":
        query = """
            SELECT agent_id, agent_name, total_revenue AS value
            FROM analytics.agent_performance_summary
            ORDER BY total_revenue DESC
            LIMIT 10
        """
    elif metric == "charters":
        query = """
            SELECT agent_id, agent_name, completed_charters AS value
            FROM analytics.agent_performance_summary
            ORDER BY completed_charters DESC
            LIMIT 10
        """
    elif metric == "conversion_rate":
        query = """
            SELECT agent_id, agent_name, conversion_rate AS value
            FROM analytics.agent_performance_summary
            WHERE total_leads > 5
            ORDER BY conversion_rate DESC
            LIMIT 10
        """
    else:
        raise HTTPException(400, f"Invalid metric: {metric}")
    
    result = db.execute(text(query))
    rankings = result.fetchall()
    
    return {
        "metric": metric,
        "period": period,
        "rankings": [
            {
                "rank": idx + 1,
                "agent_id": row.agent_id,
                "agent_name": row.agent_name,
                "value": float(row.value)
            }
            for idx, row in enumerate(rankings)
        ]
    }


@app.post("/analytics/refresh-performance")
async def refresh_performance_cache(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually refresh agent performance materialized view
    
    This should typically be run via scheduled job (cron/airflow),
    but can be triggered manually for immediate updates.
    """
    try:
        db.execute(text("REFRESH MATERIALIZED VIEW analytics.agent_performance_summary"))
        db.commit()
        
        logger.info("Performance cache refreshed successfully")
        
        return {
            "message": "Performance cache refreshed",
            "timestamp": datetime.utcnow().isoformat(),
            "success": True
        }
    except Exception as e:
        logger.error(f"Failed to refresh performance cache: {str(e)}")
        raise HTTPException(500, f"Failed to refresh cache: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
