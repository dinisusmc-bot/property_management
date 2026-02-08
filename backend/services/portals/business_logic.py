"""
Business Logic for Portals Service

Service clients and data aggregation logic for:
- Client Portal (dashboard, trips, quotes, payments)
- Vendor Portal (bid opportunities, schedule, performance)
- Admin Dashboard (system-wide analytics)
"""
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session

import config
import models
import schemas


class ServiceClient:
    """Base class for calling backend services"""
    
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
    
    async def get(self, endpoint: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}{endpoint}", headers=headers or {})
            response.raise_for_status()
            return response.json()
    
    async def post(self, endpoint: str, data: Dict[str, Any], headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request to service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}{endpoint}", json=data, headers=headers or {})
            response.raise_for_status()
            return response.json()
    
    async def put(self, endpoint: str, data: Dict[str, Any], headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Make PUT request to service"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(f"{self.base_url}{endpoint}", json=data, headers=headers or {})
            response.raise_for_status()
            return response.json()


class ClientPortalService:
    """Aggregates data for client portal"""
    
    def __init__(self):
        self.charter_client = ServiceClient(config.CHARTER_SERVICE_URL)
        self.client_client = ServiceClient(config.CLIENT_SERVICE_URL)
        self.sales_client = ServiceClient(config.SALES_SERVICE_URL)
        self.payment_client = ServiceClient(config.PAYMENT_SERVICE_URL)
        self.document_client = ServiceClient(config.DOCUMENT_SERVICE_URL)
    
    async def get_dashboard(self, user_id: int, client_id: int, auth_headers: Dict) -> schemas.ClientDashboard:
        """
        Aggregate dashboard data from multiple services.
        
        Args:
            user_id: User ID from auth
            client_id: Client entity ID
            auth_headers: Authorization headers to pass to backend services
        
        Returns:
            ClientDashboard with aggregated data
        """
        try:
            # Fetch data from multiple services in parallel
            # In production, use asyncio.gather for parallel requests
            
            # Get client info
            client_data = await self.client_client.get(f"/clients/{client_id}", headers=auth_headers)
            
            # Get charters for this client
            charters_data = await self.charter_client.get(
                f"/charters?client_id={client_id}&limit=100",
                headers=auth_headers
            )
            charters = charters_data.get("items", [])
            
            # Get quotes (from sales service)
            try:
                quotes_data = await self.sales_client.get(
                    f"/quotes?client_id={client_id}&status=pending",
                    headers=auth_headers
                )
                quotes = quotes_data.get("items", [])
            except:
                quotes = []
            
            # Calculate statistics
            total_charters = len(charters)
            active_charters = len([c for c in charters if c.get("status") in ["confirmed", "in_progress"]])
            upcoming_charters = len([c for c in charters if c.get("status") == "confirmed" and 
                                   datetime.fromisoformat(c.get("pickup_datetime", "").replace("Z", "+00:00")) > datetime.now()])
            completed_charters = len([c for c in charters if c.get("status") == "completed"])
            
            # Get recent charters (last 5)
            recent_charters = sorted(
                charters,
                key=lambda x: x.get("pickup_datetime", ""),
                reverse=True
            )[:5]
            
            # Convert to summary format
            recent_charters_summary = [
                schemas.ClientCharterSummary(
                    id=c.get("id"),
                    charter_number=c.get("charter_number"),
                    pickup_datetime=datetime.fromisoformat(c.get("pickup_datetime").replace("Z", "+00:00")),
                    dropoff_datetime=datetime.fromisoformat(c.get("dropoff_datetime").replace("Z", "+00:00")) if c.get("dropoff_datetime") else None,
                    pickup_location=c.get("pickup_location", ""),
                    destination=c.get("destination", ""),
                    passenger_count=c.get("passenger_count", 0),
                    vehicle_type=c.get("vehicle_type"),
                    status=c.get("status", ""),
                    total_amount=Decimal(str(c.get("total_amount", 0))) if c.get("total_amount") else None,
                    payment_status=c.get("payment_status"),
                    has_unread_updates=False  # TODO: Implement notification check
                )
                for c in recent_charters
            ]
            
            # Convert quotes to summary format
            pending_quotes_list = [
                schemas.ClientQuoteSummary(
                    id=q.get("id"),
                    charter_id=q.get("charter_id"),
                    quote_number=q.get("quote_number"),
                    total_amount=Decimal(str(q.get("total_amount", 0))),
                    valid_until=datetime.fromisoformat(q.get("valid_until").replace("Z", "+00:00")),
                    status=q.get("status", ""),
                    vehicle_type=q.get("vehicle_type"),
                    vendor_name=q.get("vendor_name"),
                    created_at=datetime.fromisoformat(q.get("created_at").replace("Z", "+00:00"))
                )
                for q in quotes[:5]  # Limit to 5 most recent
            ]
            
            # Calculate total spent (from payment service or charters)
            total_spent = sum(
                Decimal(str(c.get("total_amount", 0)))
                for c in charters
                if c.get("status") == "completed" and c.get("total_amount")
            )
            
            return schemas.ClientDashboard(
                user_id=user_id,
                client_name=client_data.get("name", ""),
                total_charters=total_charters,
                active_charters=active_charters,
                upcoming_charters=upcoming_charters,
                completed_charters=completed_charters,
                pending_quotes=len(quotes),
                total_spent=total_spent,
                recent_charters=recent_charters_summary,
                pending_quotes_list=pending_quotes_list,
                unread_notifications=0,  # TODO: Implement notification count
                has_pending_actions=len(quotes) > 0
            )
        
        except Exception as e:
            # Log error and return empty dashboard
            print(f"Error fetching client dashboard: {e}")
            return schemas.ClientDashboard(
                user_id=user_id,
                client_name="Unknown",
                total_charters=0,
                active_charters=0,
                upcoming_charters=0,
                completed_charters=0,
                pending_quotes=0,
                total_spent=Decimal("0"),
                recent_charters=[],
                pending_quotes_list=[],
                unread_notifications=0,
                has_pending_actions=False
            )
    
    async def get_payment_history(self, client_id: int, auth_headers: Dict, limit: int = 50) -> List[schemas.ClientPaymentHistory]:
        """Get payment history for client"""
        try:
            payments_data = await self.payment_client.get(
                f"/payments?client_id={client_id}&limit={limit}",
                headers=auth_headers
            )
            payments = payments_data.get("items", [])
            
            return [
                schemas.ClientPaymentHistory(
                    id=p.get("id"),
                    charter_id=p.get("charter_id"),
                    charter_number=p.get("charter_number"),
                    amount=Decimal(str(p.get("amount", 0))),
                    payment_method=p.get("payment_method", ""),
                    payment_date=datetime.fromisoformat(p.get("payment_date").replace("Z", "+00:00")),
                    status=p.get("status", ""),
                    receipt_url=p.get("receipt_url")
                )
                for p in payments
            ]
        except Exception as e:
            print(f"Error fetching payment history: {e}")
            return []


class VendorPortalService:
    """Aggregates data for vendor portal"""
    
    def __init__(self):
        self.vendor_client = ServiceClient(config.VENDOR_SERVICE_URL)
        self.charter_client = ServiceClient(config.CHARTER_SERVICE_URL)
        self.payment_client = ServiceClient(config.PAYMENT_SERVICE_URL)
    
    async def get_dashboard(self, user_id: int, vendor_id: int, auth_headers: Dict) -> schemas.VendorDashboard:
        """Aggregate dashboard data for vendor portal"""
        try:
            # Get vendor info and stats
            vendor_data = await self.vendor_client.get(f"/vendors/{vendor_id}", headers=auth_headers)
            vendor_stats = await self.vendor_client.get(f"/vendors/{vendor_id}/statistics", headers=auth_headers)
            
            # Get active bids
            bids_data = await self.vendor_client.get(
                f"/bids?vendor_id={vendor_id}&status=submitted",
                headers=auth_headers
            )
            active_bids = len(bids_data.get("items", []))
            
            # Get bid opportunities (open charters)
            try:
                opportunities_data = await self.charter_client.get(
                    "/charters?status=pending&needs_vendor=true&limit=10",
                    headers=auth_headers
                )
                opportunities = opportunities_data.get("items", [])
            except:
                opportunities = []
            
            # Get upcoming trips (accepted bids with upcoming charters)
            try:
                trips_data = await self.charter_client.get(
                    f"/charters?vendor_id={vendor_id}&status=confirmed&limit=10",
                    headers=auth_headers
                )
                trips = trips_data.get("items", [])
            except:
                trips = []
            
            # Get compliance status
            try:
                compliance_data = await self.vendor_client.get(
                    f"/vendors/{vendor_id}/compliance/status",
                    headers=auth_headers
                )
                compliance_status = "compliant" if compliance_data.get("is_compliant") else "missing_docs"
                expiring_documents = compliance_data.get("expiring_soon", 0)
            except:
                compliance_status = "unknown"
                expiring_documents = 0
            
            # Convert opportunities to schema
            bid_opportunities = [
                schemas.VendorBidOpportunity(
                    charter_id=o.get("id"),
                    charter_number=o.get("charter_number"),
                    pickup_datetime=datetime.fromisoformat(o.get("pickup_datetime").replace("Z", "+00:00")),
                    pickup_location=o.get("pickup_location", ""),
                    destination=o.get("destination", ""),
                    distance_miles=Decimal(str(o.get("distance_miles", 0))) if o.get("distance_miles") else None,
                    passenger_count=o.get("passenger_count", 0),
                    vehicle_type=o.get("vehicle_type"),
                    bid_deadline=datetime.fromisoformat(o.get("bid_deadline").replace("Z", "+00:00")) if o.get("bid_deadline") else None,
                    current_bids_count=o.get("bids_count", 0),
                    client_rating=Decimal(str(o.get("client_rating", 0))) if o.get("client_rating") else None
                )
                for o in opportunities[:5]
            ]
            
            # Convert trips to schema
            scheduled_trips = [
                schemas.VendorScheduledTrip(
                    charter_id=t.get("id"),
                    charter_number=t.get("charter_number"),
                    pickup_datetime=datetime.fromisoformat(t.get("pickup_datetime").replace("Z", "+00:00")),
                    dropoff_datetime=datetime.fromisoformat(t.get("dropoff_datetime").replace("Z", "+00:00")) if t.get("dropoff_datetime") else None,
                    pickup_location=t.get("pickup_location", ""),
                    destination=t.get("destination", ""),
                    passenger_count=t.get("passenger_count", 0),
                    vehicle_assigned=t.get("vehicle_assigned"),
                    driver_assigned=t.get("driver_assigned"),
                    special_requirements=t.get("special_requirements", [])
                )
                for t in trips[:5]
            ]
            
            return schemas.VendorDashboard(
                vendor_id=vendor_id,
                vendor_name=vendor_data.get("business_name", ""),
                total_bids_submitted=vendor_stats.get("total_bids_submitted", 0),
                bids_won=vendor_stats.get("bids_won", 0),
                win_rate_percentage=Decimal(str(vendor_stats.get("win_rate_percentage", 0))) if vendor_stats.get("win_rate_percentage") else None,
                average_rating=Decimal(str(vendor_stats.get("average_rating", 0))) if vendor_stats.get("average_rating") else None,
                total_completed_trips=vendor_stats.get("completed_trips", 0),
                total_earnings=Decimal(str(vendor_stats.get("total_earnings", 0))),
                pending_payments=Decimal(str(vendor_stats.get("pending_payments", 0))),
                active_bids=active_bids,
                upcoming_trips=len(trips),
                bid_opportunities=bid_opportunities,
                scheduled_trips=scheduled_trips,
                compliance_status=compliance_status,
                expiring_documents=expiring_documents,
                unread_notifications=0  # TODO: Implement
            )
        
        except Exception as e:
            print(f"Error fetching vendor dashboard: {e}")
            return schemas.VendorDashboard(
                vendor_id=vendor_id,
                vendor_name="Unknown",
                total_bids_submitted=0,
                bids_won=0,
                win_rate_percentage=None,
                average_rating=None,
                total_completed_trips=0,
                total_earnings=Decimal("0"),
                pending_payments=Decimal("0"),
                active_bids=0,
                upcoming_trips=0,
                bid_opportunities=[],
                scheduled_trips=[],
                compliance_status="unknown",
                expiring_documents=0,
                unread_notifications=0
            )


class AdminDashboardService:
    """Aggregates system-wide data for admin dashboard"""
    
    def __init__(self):
        self.auth_client = ServiceClient(config.AUTH_SERVICE_URL)
        self.charter_client = ServiceClient(config.CHARTER_SERVICE_URL)
        self.client_client = ServiceClient(config.CLIENT_SERVICE_URL)
        self.vendor_client = ServiceClient(config.VENDOR_SERVICE_URL)
        self.payment_client = ServiceClient(config.PAYMENT_SERVICE_URL)
    
    async def get_dashboard(self, auth_headers: Dict) -> schemas.AdminDashboard:
        """Aggregate system-wide dashboard data"""
        try:
            # Get counts from various services
            # In production, these would be actual API calls
            
            # System statistics
            system_stats = schemas.AdminSystemStats(
                total_users=0,  # TODO: Get from auth service
                total_clients=0,  # TODO: Get from client service
                total_vendors=0,  # TODO: Get from vendor service
                active_charters=0,  # TODO: Get from charter service
                total_revenue=Decimal("0"),  # TODO: Get from payment service
                pending_approvals=0  # TODO: Aggregate from various services
            )
            
            # Recent activity (would come from activity logs)
            recent_activity = []
            
            return schemas.AdminDashboard(
                system_stats=system_stats,
                recent_activity=recent_activity,
                new_charters_today=0,
                new_users_today=0,
                revenue_today=Decimal("0"),
                pending_vendor_approvals=0,
                pending_charter_approvals=0,
                pending_change_requests=0,
                system_alerts=[]
            )
        
        except Exception as e:
            print(f"Error fetching admin dashboard: {e}")
            return schemas.AdminDashboard(
                system_stats=schemas.AdminSystemStats(
                    total_users=0,
                    total_clients=0,
                    total_vendors=0,
                    active_charters=0,
                    total_revenue=Decimal("0"),
                    pending_approvals=0
                ),
                recent_activity=[],
                new_charters_today=0,
                new_users_today=0,
                revenue_today=Decimal("0"),
                pending_vendor_approvals=0,
                pending_charter_approvals=0,
                pending_change_requests=0,
                system_alerts=[]
            )


class PreferenceService:
    """Manage user preferences"""
    
    def get_preferences(self, db: Session, user_id: int) -> Optional[models.PortalUserPreference]:
        """Get user preferences"""
        return db.query(models.PortalUserPreference).filter(
            models.PortalUserPreference.user_id == user_id
        ).first()
    
    def create_preferences(self, db: Session, preferences: schemas.PortalUserPreferenceCreate) -> models.PortalUserPreference:
        """Create user preferences"""
        db_prefs = models.PortalUserPreference(**preferences.dict())
        db.add(db_prefs)
        db.commit()
        db.refresh(db_prefs)
        return db_prefs
    
    def update_preferences(self, db: Session, user_id: int, updates: schemas.PortalUserPreferenceUpdate) -> Optional[models.PortalUserPreference]:
        """Update user preferences"""
        db_prefs = self.get_preferences(db, user_id)
        if not db_prefs:
            return None
        
        update_data = updates.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_prefs, field, value)
        
        db.commit()
        db.refresh(db_prefs)
        return db_prefs
