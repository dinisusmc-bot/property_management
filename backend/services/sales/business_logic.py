"""
Business logic for Sales Service
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, date, timedelta
from typing import Optional, List
import httpx
import logging

from models import Lead, LeadActivity, AssignmentRule, LeadStatus
import config

logger = logging.getLogger(__name__)


class LeadAssignmentService:
    """Service for assigning leads to sales agents"""
    
    @staticmethod
    async def assign_lead_to_agent(db: Session, lead: Lead) -> Optional[int]:
        """
        Assign lead to an agent using round-robin logic
        Returns assigned agent_id or None if no agents available
        """
        # Check if lead email matches existing client
        existing_client = await LeadAssignmentService._check_existing_client(lead.email)
        if existing_client and existing_client.get("assigned_agent_id"):
            logger.info(f"Lead {lead.id} matches existing client, assigning to agent {existing_client['assigned_agent_id']}")
            return existing_client["assigned_agent_id"]
        
        # Get active assignment rules
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        rules = db.query(AssignmentRule).filter(
            AssignmentRule.is_active == True
        ).order_by(
            AssignmentRule.last_assigned_at.asc().nullsfirst()
        ).all()
        
        if not rules:
            logger.warning("No active assignment rules found")
            return None
        
        # Reset daily counters if needed
        for rule in rules:
            if rule.last_reset_date is None or rule.last_reset_date.date() < today:
                rule.leads_assigned_today = 0
                rule.last_reset_date = datetime.now()
                db.add(rule)
        
        # Find agent with capacity
        for rule in rules:
            if rule.leads_assigned_today < rule.max_leads_per_day:
                # Assign to this agent
                rule.last_assigned_at = datetime.now()
                rule.total_leads_assigned += 1
                rule.leads_assigned_today += 1
                db.add(rule)
                db.commit()
                
                logger.info(f"Assigned lead {lead.id} to agent {rule.agent_id}")
                return rule.agent_id
        
        logger.warning(f"All agents at capacity, lead {lead.id} not assigned")
        return None
    
    @staticmethod
    async def _check_existing_client(email: str) -> Optional[dict]:
        """Check if client exists in Client Service"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config.CLIENT_SERVICE_URL}/api/v1/clients/by-email/{email}",
                    timeout=5.0
                )
                if response.status_code == 200:
                    return response.json()
        except Exception as e:
            logger.error(f"Error checking existing client: {e}")
        return None


class LeadConversionService:
    """Service for converting leads to charters"""
    
    @staticmethod
    async def convert_lead(db: Session, lead: Lead, user_id: int) -> dict:
        """
        Convert lead to client and charter
        Returns dict with client_id and charter_id
        """
        result = {
            "client_id": None,
            "charter_id": None,
            "errors": []
        }
        
        # Step 1: Create or get client
        try:
            client_data = {
                "name": f"{lead.first_name} {lead.last_name}",
                "type": "personal" if not lead.company_name else "corporate",
                "email": lead.email,
                "phone": lead.phone or "",
                "company_name": lead.company_name
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.CLIENT_SERVICE_URL}/api/v1/clients",
                    json=client_data,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    client_response = response.json()
                    result["client_id"] = client_response.get("id")
                    logger.info(f"Created client {result['client_id']} from lead {lead.id}")
                else:
                    result["errors"].append(f"Client creation failed: {response.text}")
                    return result
                    
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            result["errors"].append(f"Client creation error: {str(e)}")
            return result
        
        # Step 2: Create charter quote
        try:
            charter_data = {
                "client_id": result["client_id"],
                "status": "quote",
                "trip_date": lead.estimated_trip_date.isoformat() if lead.estimated_trip_date else None,
                "passengers": lead.estimated_passengers or 1,
                "notes": lead.trip_details or "",
                "trip_hours": 8,  # Default
                "is_overnight": False,
                "is_weekend": False
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.CHARTER_SERVICE_URL}/api/v1/charters",
                    json=charter_data,
                    timeout=10.0
                )
                
                if response.status_code in [200, 201]:
                    charter_response = response.json()
                    result["charter_id"] = charter_response.get("id")
                    logger.info(f"Created charter {result['charter_id']} from lead {lead.id}")
                else:
                    result["errors"].append(f"Charter creation failed: {response.text}")
                    return result
                    
        except Exception as e:
            logger.error(f"Error creating charter: {e}")
            result["errors"].append(f"Charter creation error: {str(e)}")
            return result
        
        # Step 3: Update lead status
        lead.status = LeadStatus.CONVERTED
        lead.converted_to_client_id = result["client_id"]
        lead.converted_to_charter_id = result["charter_id"]
        lead.converted_at = datetime.now()
        db.add(lead)
        
        # Step 4: Log activity
        activity = LeadActivity(
            lead_id=lead.id,
            activity_type="status_change",
            subject="Lead Converted",
            details=f"Converted to client ID {result['client_id']} and charter ID {result['charter_id']}",
            performed_by=user_id
        )
        db.add(activity)
        db.commit()
        
        return result
