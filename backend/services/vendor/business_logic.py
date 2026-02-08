"""
Business logic for Vendor Service
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from models import Vendor, Bid, VendorRating, VendorCompliance, BidRequest, BidStatus, VendorStatus
from schemas import BidCreate, VendorRatingCreate
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

logger = logging.getLogger(__name__)


class VendorService:
    """Business logic for vendor management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_vendor_stats(self, vendor_id: int) -> Dict:
        """Calculate and update vendor statistics"""
        vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            return {}
        
        # Calculate ratings
        ratings = self.db.query(VendorRating).filter(
            VendorRating.vendor_id == vendor_id
        ).all()
        
        if ratings:
            avg_rating = sum(r.overall_rating for r in ratings) / len(ratings)
            vendor.average_rating = round(avg_rating, 2)
            vendor.total_ratings = len(ratings)
        
        # Calculate bid statistics
        all_bids = self.db.query(Bid).filter(Bid.vendor_id == vendor_id).all()
        vendor.total_bids_submitted = len([b for b in all_bids if b.status == BidStatus.SUBMITTED])
        vendor.bids_won = len([b for b in all_bids if b.status == BidStatus.ACCEPTED])
        vendor.bids_lost = len([b for b in all_bids if b.status == BidStatus.REJECTED])
        
        if vendor.total_bids_submitted > 0:
            vendor.win_rate_percentage = round(
                (vendor.bids_won / vendor.total_bids_submitted) * 100, 2
            )
        
        self.db.commit()
        self.db.refresh(vendor)
        
        logger.info(f"Updated stats for vendor {vendor_id}: {vendor.bids_won}/{vendor.total_bids_submitted} won")
        
        return {
            "average_rating": vendor.average_rating,
            "total_ratings": vendor.total_ratings,
            "win_rate_percentage": vendor.win_rate_percentage,
            "bids_won": vendor.bids_won
        }
    
    def check_vendor_eligibility(self, vendor_id: int) -> tuple[bool, str]:
        """Check if vendor is eligible to submit bids"""
        vendor = self.db.query(Vendor).filter(Vendor.id == vendor_id).first()
        
        if not vendor:
            return False, "Vendor not found"
        
        if vendor.status != VendorStatus.ACTIVE:
            return False, f"Vendor status is {vendor.status}, must be ACTIVE"
        
        if not vendor.is_verified:
            return False, "Vendor is not verified"
        
        # Check for valid insurance
        if vendor.insurance_expiration:
            if vendor.insurance_expiration < datetime.now().date():
                return False, "Insurance has expired"
        
        # Check compliance documents
        required_docs = ["business_license", "insurance_certificate"]
        for doc_type in required_docs:
            doc = self.db.query(VendorCompliance).filter(
                and_(
                    VendorCompliance.vendor_id == vendor_id,
                    VendorCompliance.document_type == doc_type,
                    VendorCompliance.status == "approved"
                )
            ).first()
            
            if not doc:
                return False, f"Missing required document: {doc_type}"
            
            # Check expiration
            if doc.expiration_date and doc.expiration_date < datetime.now().date():
                return False, f"Document {doc_type} has expired"
        
        return True, "Eligible"
    
    def get_top_vendors(self, limit: int = 10) -> List[Vendor]:
        """Get top-rated vendors"""
        return self.db.query(Vendor).filter(
            and_(
                Vendor.status == VendorStatus.ACTIVE,
                Vendor.is_verified == True,
                Vendor.average_rating >= 4.0,
                Vendor.total_ratings >= 3
            )
        ).order_by(
            Vendor.average_rating.desc(),
            Vendor.total_ratings.desc()
        ).limit(limit).all()
    
    def find_matching_vendors(
        self,
        service_state: Optional[str] = None,
        passenger_capacity: Optional[int] = None,
        service_radius_miles: Optional[int] = None
    ) -> List[Vendor]:
        """Find vendors matching trip requirements"""
        query = self.db.query(Vendor).filter(
            and_(
                Vendor.status == VendorStatus.ACTIVE,
                Vendor.is_verified == True
            )
        )
        
        if service_state:
            # Check if state is in their service states JSON array
            query = query.filter(
                Vendor.service_states.contains([service_state])
            )
        
        if passenger_capacity:
            query = query.filter(
                Vendor.max_passenger_capacity >= passenger_capacity
            )
        
        if service_radius_miles:
            query = query.filter(
                Vendor.service_radius_miles >= service_radius_miles
            )
        
        vendors = query.order_by(
            Vendor.is_preferred.desc(),
            Vendor.average_rating.desc()
        ).all()
        
        logger.info(f"Found {len(vendors)} matching vendors")
        return vendors


class BidService:
    """Business logic for bid management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def rank_bids_for_charter(self, charter_id: int):
        """Rank all bids for a charter by price"""
        bids = self.db.query(Bid).filter(
            and_(
                Bid.charter_id == charter_id,
                Bid.status == BidStatus.SUBMITTED
            )
        ).order_by(Bid.quoted_price.asc()).all()
        
        if not bids:
            return
        
        lowest_price = bids[0].quoted_price
        
        for idx, bid in enumerate(bids, start=1):
            bid.rank = idx
            bid.is_lowest_bid = (idx == 1)
            bid.price_difference_from_lowest = round(bid.quoted_price - lowest_price, 2)
        
        self.db.commit()
        logger.info(f"Ranked {len(bids)} bids for charter {charter_id}")
    
    def check_bid_validity(self, bid_id: int) -> tuple[bool, str]:
        """Check if a bid is still valid"""
        bid = self.db.query(Bid).filter(Bid.id == bid_id).first()
        
        if not bid:
            return False, "Bid not found"
        
        if bid.status not in [BidStatus.SUBMITTED, BidStatus.UNDER_REVIEW]:
            return False, f"Bid status is {bid.status}"
        
        if bid.valid_until < datetime.now():
            bid.status = BidStatus.EXPIRED
            self.db.commit()
            return False, "Bid has expired"
        
        return True, "Valid"
    
    def accept_bid(self, bid_id: int, accepted_by: int, reason: Optional[str] = None) -> Bid:
        """Accept a bid and reject others for the same charter"""
        bid = self.db.query(Bid).filter(Bid.id == bid_id).first()
        
        if not bid:
            raise ValueError("Bid not found")
        
        # Check if bid is still valid
        valid, message = self.check_bid_validity(bid_id)
        if not valid:
            raise ValueError(f"Cannot accept bid: {message}")
        
        # Accept this bid
        bid.status = BidStatus.ACCEPTED
        bid.decided_at = datetime.now()
        bid.decision_reason = reason or "Bid accepted"
        
        # Reject all other submitted bids for this charter
        other_bids = self.db.query(Bid).filter(
            and_(
                Bid.charter_id == bid.charter_id,
                Bid.id != bid_id,
                Bid.status.in_([BidStatus.SUBMITTED, BidStatus.UNDER_REVIEW])
            )
        ).all()
        
        for other_bid in other_bids:
            other_bid.status = BidStatus.REJECTED
            other_bid.decided_at = datetime.now()
            other_bid.decision_reason = "Another bid was accepted"
        
        self.db.commit()
        self.db.refresh(bid)
        
        logger.info(f"Accepted bid {bid_id} for charter {bid.charter_id}, rejected {len(other_bids)} others")
        
        # Update vendor stats
        vendor_service = VendorService(self.db)
        vendor_service.calculate_vendor_stats(bid.vendor_id)
        
        return bid
    
    def reject_bid(self, bid_id: int, rejected_by: int, reason: Optional[str] = None) -> Bid:
        """Reject a bid"""
        bid = self.db.query(Bid).filter(Bid.id == bid_id).first()
        
        if not bid:
            raise ValueError("Bid not found")
        
        if bid.status not in [BidStatus.SUBMITTED, BidStatus.UNDER_REVIEW]:
            raise ValueError(f"Cannot reject bid with status {bid.status}")
        
        bid.status = BidStatus.REJECTED
        bid.decided_at = datetime.now()
        bid.decision_reason = reason or "Bid rejected"
        
        self.db.commit()
        self.db.refresh(bid)
        
        logger.info(f"Rejected bid {bid_id}")
        
        # Update vendor stats
        vendor_service = VendorService(self.db)
        vendor_service.calculate_vendor_stats(bid.vendor_id)
        
        return bid
    
    def get_bid_comparison(self, charter_id: int) -> Dict:
        """Get comparison of all bids for a charter"""
        bids = self.db.query(Bid).filter(
            and_(
                Bid.charter_id == charter_id,
                Bid.status == BidStatus.SUBMITTED
            )
        ).all()
        
        if not bids:
            return {
                "charter_id": charter_id,
                "total_bids": 0,
                "lowest_bid": None,
                "highest_bid": None,
                "average_bid": None,
                "bids": []
            }
        
        prices = [bid.quoted_price for bid in bids]
        
        return {
            "charter_id": charter_id,
            "total_bids": len(bids),
            "lowest_bid": min(prices),
            "highest_bid": max(prices),
            "average_bid": round(sum(prices) / len(prices), 2),
            "bids": bids
        }
    
    def expire_old_bids(self):
        """Mark expired bids as expired (background task)"""
        expired_bids = self.db.query(Bid).filter(
            and_(
                Bid.valid_until < datetime.now(),
                Bid.status.in_([BidStatus.SUBMITTED, BidStatus.UNDER_REVIEW])
            )
        ).all()
        
        for bid in expired_bids:
            bid.status = BidStatus.EXPIRED
        
        self.db.commit()
        
        logger.info(f"Expired {len(expired_bids)} old bids")
        return len(expired_bids)


class RatingService:
    """Business logic for vendor ratings"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def can_rate_vendor(self, vendor_id: int, charter_id: int, user_id: int) -> tuple[bool, str]:
        """Check if user can rate this vendor for this charter"""
        # Check if rating already exists
        existing = self.db.query(VendorRating).filter(
            and_(
                VendorRating.vendor_id == vendor_id,
                VendorRating.charter_id == charter_id,
                VendorRating.rated_by == user_id
            )
        ).first()
        
        if existing:
            return False, "You have already rated this vendor for this charter"
        
        # Check if there's an accepted bid
        accepted_bid = self.db.query(Bid).filter(
            and_(
                Bid.vendor_id == vendor_id,
                Bid.charter_id == charter_id,
                Bid.status == BidStatus.ACCEPTED
            )
        ).first()
        
        if not accepted_bid:
            return False, "No accepted bid found for this vendor and charter"
        
        return True, "Can rate"
    
    def create_rating(
        self,
        rating_data: VendorRatingCreate,
        rated_by: int
    ) -> VendorRating:
        """Create a new vendor rating and update vendor stats"""
        # Check if can rate
        can_rate, message = self.can_rate_vendor(
            rating_data.vendor_id,
            rating_data.charter_id,
            rated_by
        )
        
        if not can_rate:
            raise ValueError(message)
        
        # Create rating
        rating = VendorRating(
            **rating_data.model_dump(),
            rated_by=rated_by,
            is_verified=True  # Since we verified there's an accepted bid
        )
        
        self.db.add(rating)
        self.db.commit()
        self.db.refresh(rating)
        
        logger.info(f"Created rating {rating.id} for vendor {rating.vendor_id}")
        
        # Update vendor stats
        vendor_service = VendorService(self.db)
        vendor_service.calculate_vendor_stats(rating.vendor_id)
        
        return rating


class ComplianceService:
    """Business logic for compliance management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_expiring_documents(self, days_ahead: int = 30) -> List[VendorCompliance]:
        """Find documents expiring soon"""
        cutoff_date = datetime.now().date() + timedelta(days=days_ahead)
        
        expiring = self.db.query(VendorCompliance).filter(
            and_(
                VendorCompliance.status == "approved",
                VendorCompliance.expiration_date.isnot(None),
                VendorCompliance.expiration_date <= cutoff_date,
                VendorCompliance.expiration_date >= datetime.now().date()
            )
        ).all()
        
        logger.info(f"Found {len(expiring)} documents expiring in next {days_ahead} days")
        return expiring
    
    def get_vendor_compliance_status(self, vendor_id: int) -> Dict:
        """Get overall compliance status for a vendor"""
        from config import REQUIRED_COMPLIANCE_DOCS
        
        docs = self.db.query(VendorCompliance).filter(
            VendorCompliance.vendor_id == vendor_id
        ).all()
        
        status = {
            "vendor_id": vendor_id,
            "total_documents": len(docs),
            "approved_documents": len([d for d in docs if d.status == "approved"]),
            "pending_documents": len([d for d in docs if d.status == "pending"]),
            "expired_documents": len([d for d in docs if d.status == "expired"]),
            "rejected_documents": len([d for d in docs if d.status == "rejected"]),
            "missing_required": [],
            "is_compliant": False
        }
        
        # Check required documents
        for required_type in REQUIRED_COMPLIANCE_DOCS:
            approved_doc = next(
                (d for d in docs if d.document_type == required_type and d.status == "approved"),
                None
            )
            if not approved_doc:
                status["missing_required"].append(required_type)
        
        status["is_compliant"] = len(status["missing_required"]) == 0
        
        return status
