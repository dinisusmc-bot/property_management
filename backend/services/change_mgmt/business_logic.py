"""
Business logic for change management service
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
import httpx

import config
import models
import schemas


class ChangeWorkflowService:
    """Service for managing change case workflows and state transitions"""
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        models.ChangeStatus.PENDING: [
            models.ChangeStatus.UNDER_REVIEW,
            models.ChangeStatus.CANCELLED
        ],
        models.ChangeStatus.UNDER_REVIEW: [
            models.ChangeStatus.APPROVED,
            models.ChangeStatus.REJECTED,
            models.ChangeStatus.CANCELLED
        ],
        models.ChangeStatus.APPROVED: [
            models.ChangeStatus.IMPLEMENTED,
            models.ChangeStatus.CANCELLED
        ],
        models.ChangeStatus.REJECTED: [
            models.ChangeStatus.CANCELLED
        ],
        models.ChangeStatus.IMPLEMENTED: [],
        models.ChangeStatus.CANCELLED: []
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.history_service = AuditService(db)
        self.notification_service = NotificationService(db)
    
    def create_change_case(
        self,
        change_data: schemas.ChangeCaseCreate,
        user_info: Optional[Dict[str, Any]] = None
    ) -> models.ChangeCase:
        """Create a new change case"""
        
        # Calculate price difference if both prices provided
        price_difference = None
        if change_data.current_price and change_data.proposed_price:
            price_difference = change_data.proposed_price - change_data.current_price
        
        # Determine if approval is required
        requires_approval = self._requires_approval(change_data, price_difference)
        
        # Generate case number
        case_number = self._generate_case_number()
        
        # Create change case
        now = datetime.utcnow()
        change_case = models.ChangeCase(
            case_number=case_number,
            charter_id=change_data.charter_id,
            client_id=change_data.client_id,
            vendor_id=change_data.vendor_id,
            change_type=change_data.change_type,
            priority=change_data.priority,
            status=models.ChangeStatus.PENDING,
            title=change_data.title,
            description=change_data.description,
            reason=change_data.reason,
            requested_by=change_data.requested_by,
            requested_by_name=change_data.requested_by_name,
            requested_at=now,
            impact_level=change_data.impact_level,
            impact_assessment=change_data.impact_assessment,
            affects_vendor=change_data.affects_vendor,
            affects_pricing=change_data.affects_pricing,
            affects_schedule=change_data.affects_schedule,
            current_price=change_data.current_price,
            proposed_price=change_data.proposed_price,
            price_difference=price_difference,
            proposed_changes=change_data.proposed_changes,
            requires_approval=requires_approval,
            tags=change_data.tags or [],
            due_date=change_data.due_date,
            created_at=now,
            updated_at=now
        )
        
        self.db.add(change_case)
        self.db.commit()
        self.db.refresh(change_case)
        
        # Log creation in history
        self.history_service.log_action(
            change_case_id=change_case.id,
            action="created",
            action_by=change_data.requested_by,
            action_by_name=change_data.requested_by_name,
            new_status=models.ChangeStatus.PENDING,
            notes=f"Change case created: {change_data.title}",
            user_info=user_info
        )
        
        # Send notifications
        self.notification_service.notify_change_created(change_case)
        
        return change_case
    
    def update_change_case(
        self,
        case_id: int,
        update_data: schemas.ChangeCaseUpdate,
        updated_by: int,
        updated_by_name: str,
        user_info: Optional[Dict[str, Any]] = None
    ) -> models.ChangeCase:
        """Update an existing change case"""
        
        change_case = self.db.query(models.ChangeCase).filter(
            models.ChangeCase.id == case_id
        ).first()
        
        if not change_case:
            raise ValueError(f"Change case {case_id} not found")
        
        if change_case.status not in [models.ChangeStatus.PENDING, models.ChangeStatus.UNDER_REVIEW]:
            raise ValueError(f"Cannot update change case in {change_case.status.value} status")
        
        # Track field changes
        field_changes = {}
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for field, new_value in update_dict.items():
            old_value = getattr(change_case, field)
            if old_value != new_value:
                field_changes[field] = {
                    "old": str(old_value),
                    "new": str(new_value)
                }
                setattr(change_case, field, new_value)
        
        # Recalculate price difference if price updated
        if "proposed_price" in update_dict and change_case.current_price:
            change_case.price_difference = change_case.proposed_price - change_case.current_price
        
        change_case.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(change_case)
        
        # Log update
        if field_changes:
            self.history_service.log_action(
                change_case_id=change_case.id,
                action="updated",
                action_by=updated_by,
                action_by_name=updated_by_name,
                notes="Change case updated",
                field_changes=field_changes,
                user_info=user_info
            )
        
        return change_case
    
    def transition_to_review(
        self,
        case_id: int,
        reviewed_by: int,
        reviewed_by_name: str,
        user_info: Optional[Dict[str, Any]] = None
    ) -> models.ChangeCase:
        """Move change case to under review"""
        return self._transition_status(
            case_id=case_id,
            new_status=models.ChangeStatus.UNDER_REVIEW,
            action_by=reviewed_by,
            action_by_name=reviewed_by_name,
            action="moved_to_review",
            notes="Change case moved to review",
            user_info=user_info
        )
    
    def approve_change(
        self,
        case_id: int,
        approval_data: schemas.ApproveChangeRequest,
        user_info: Optional[Dict[str, Any]] = None
    ) -> models.ChangeCase:
        """Approve a change case"""
        
        change_case = self._transition_status(
            case_id=case_id,
            new_status=models.ChangeStatus.APPROVED,
            action_by=approval_data.approved_by,
            action_by_name=approval_data.approved_by_name,
            action="approved",
            notes=approval_data.approval_notes or "Change approved",
            user_info=user_info
        )
        
        # Update approval fields
        change_case.approved_by = approval_data.approved_by
        change_case.approved_at = datetime.utcnow()
        change_case.approval_notes = approval_data.approval_notes
        
        self.db.commit()
        self.db.refresh(change_case)
        
        # Notify relevant parties
        self.notification_service.notify_change_approved(change_case)
        
        return change_case
    
    def reject_change(
        self,
        case_id: int,
        rejection_data: schemas.RejectChangeRequest,
        user_info: Optional[Dict[str, Any]] = None
    ) -> models.ChangeCase:
        """Reject a change case"""
        
        change_case = self._transition_status(
            case_id=case_id,
            new_status=models.ChangeStatus.REJECTED,
            action_by=rejection_data.rejected_by,
            action_by_name=rejection_data.rejected_by_name,
            action="rejected",
            notes=rejection_data.rejection_reason,
            user_info=user_info
        )
        
        # Update rejection fields
        change_case.rejected_by = rejection_data.rejected_by
        change_case.rejected_at = datetime.utcnow()
        change_case.rejection_reason = rejection_data.rejection_reason
        
        self.db.commit()
        self.db.refresh(change_case)
        
        # Notify relevant parties
        self.notification_service.notify_change_rejected(change_case)
        
        return change_case
    
    def implement_change(
        self,
        case_id: int,
        implementation_data: schemas.ImplementChangeRequest,
        user_info: Optional[Dict[str, Any]] = None
    ) -> models.ChangeCase:
        """Mark change as implemented"""
        
        change_case = self._transition_status(
            case_id=case_id,
            new_status=models.ChangeStatus.IMPLEMENTED,
            action_by=implementation_data.implemented_by,
            action_by_name=implementation_data.implemented_by_name,
            action="implemented",
            notes=implementation_data.implementation_notes or "Change implemented",
            user_info=user_info
        )
        
        # Update implementation fields
        change_case.implemented_by = implementation_data.implemented_by
        change_case.implemented_at = datetime.utcnow()
        change_case.implementation_notes = implementation_data.implementation_notes
        change_case.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(change_case)
        
        # Notify relevant parties
        self.notification_service.notify_change_implemented(change_case)
        
        return change_case
    
    def cancel_change(
        self,
        case_id: int,
        cancellation_data: schemas.CancelChangeRequest,
        user_info: Optional[Dict[str, Any]] = None
    ) -> models.ChangeCase:
        """Cancel a change case"""
        
        change_case = self._transition_status(
            case_id=case_id,
            new_status=models.ChangeStatus.CANCELLED,
            action_by=cancellation_data.cancelled_by,
            action_by_name=cancellation_data.cancelled_by_name,
            action="cancelled",
            notes=cancellation_data.cancellation_reason,
            user_info=user_info
        )
        
        change_case.completed_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(change_case)
        
        return change_case
    
    def _transition_status(
        self,
        case_id: int,
        new_status: models.ChangeStatus,
        action_by: int,
        action_by_name: str,
        action: str,
        notes: str,
        user_info: Optional[Dict[str, Any]] = None
    ) -> models.ChangeCase:
        """Internal method to handle status transitions"""
        
        change_case = self.db.query(models.ChangeCase).filter(
            models.ChangeCase.id == case_id
        ).first()
        
        if not change_case:
            raise ValueError(f"Change case {case_id} not found")
        
        # Validate transition
        if new_status not in self.VALID_TRANSITIONS.get(change_case.status, []):
            raise ValueError(
                f"Invalid transition from {change_case.status.value} to {new_status.value}"
            )
        
        old_status = change_case.status
        change_case.status = new_status
        change_case.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(change_case)
        
        # Log transition
        self.history_service.log_action(
            change_case_id=change_case.id,
            action=action,
            action_by=action_by,
            action_by_name=action_by_name,
            previous_status=old_status,
            new_status=new_status,
            notes=notes,
            user_info=user_info
        )
        
        return change_case
    
    def _requires_approval(
        self,
        change_data: schemas.ChangeCaseCreate,
        price_difference: Optional[float]
    ) -> bool:
        """Determine if change requires approval"""
        
        # Always require approval for cancellations
        if change_data.change_type == models.ChangeType.CANCELLATION:
            return True
        
        # Require approval if affects pricing
        if change_data.affects_pricing:
            return True
        
        # Require approval if price difference exceeds threshold
        if price_difference and abs(price_difference) >= config.REQUIRE_MANAGER_APPROVAL_THRESHOLD:
            return True
        
        # Require approval for high/urgent priority
        if change_data.priority in [models.ChangePriority.HIGH, models.ChangePriority.URGENT]:
            return True
        
        # Require approval for significant/major impact
        if change_data.impact_level in [models.ImpactLevel.SIGNIFICANT, models.ImpactLevel.MAJOR]:
            return True
        
        # Auto-approve minor changes if configured
        if config.AUTO_APPROVE_MINOR_CHANGES and change_data.impact_level == models.ImpactLevel.MINIMAL:
            return False
        
        return True
    
    def _generate_case_number(self) -> str:
        """Generate unique case number (CHG-YYYY-NNNN)"""
        year = datetime.utcnow().year
        
        # Get count of cases this year
        count = self.db.query(func.count(models.ChangeCase.id)).filter(
            func.extract('year', models.ChangeCase.created_at) == year
        ).scalar() or 0
        
        return f"CHG-{year}-{count + 1:04d}"


class ApprovalService:
    """Service for managing change approvals"""
    
    def __init__(self, db: Session):
        self.db = db
        self.history_service = AuditService(db)
    
    def add_approver(
        self,
        approval_data: schemas.ChangeApprovalCreate
    ) -> models.ChangeApproval:
        """Add an approver to a change case"""
        
        approval = models.ChangeApproval(
            change_case_id=approval_data.change_case_id,
            approver_id=approval_data.approver_id,
            approver_name=approval_data.approver_name,
            approver_role=approval_data.approver_role,
            approval_level=approval_data.approval_level,
            required=approval_data.required,
            status=models.ApprovalStatus.PENDING,
            conditions=approval_data.conditions,
            requested_at=datetime.utcnow()
        )
        
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        
        return approval
    
    def update_approval(
        self,
        approval_id: int,
        update_data: schemas.ChangeApprovalUpdate
    ) -> models.ChangeApproval:
        """Update approval status"""
        
        approval = self.db.query(models.ChangeApproval).filter(
            models.ChangeApproval.id == approval_id
        ).first()
        
        if not approval:
            raise ValueError(f"Approval {approval_id} not found")
        
        approval.status = update_data.status
        approval.decision = update_data.decision
        approval.notes = update_data.notes
        approval.responded_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(approval)
        
        return approval
    
    def get_pending_approvals(
        self,
        approver_id: int,
        limit: int = 50
    ) -> List[models.ChangeApproval]:
        """Get pending approvals for an approver"""
        
        return self.db.query(models.ChangeApproval).filter(
            and_(
                models.ChangeApproval.approver_id == approver_id,
                models.ChangeApproval.status == models.ApprovalStatus.PENDING
            )
        ).order_by(models.ChangeApproval.requested_at.desc()).limit(limit).all()


class AuditService:
    """Service for audit logging"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        change_case_id: int,
        action: str,
        action_by: int,
        action_by_name: str,
        previous_status: Optional[models.ChangeStatus] = None,
        new_status: Optional[models.ChangeStatus] = None,
        notes: Optional[str] = None,
        field_changes: Optional[Dict[str, Any]] = None,
        system_generated: bool = False,
        user_info: Optional[Dict[str, Any]] = None
    ) -> models.ChangeHistory:
        """Log an action in change history"""
        
        history = models.ChangeHistory(
            change_case_id=change_case_id,
            action=action,
            action_by=action_by,
            action_by_name=action_by_name,
            action_at=datetime.utcnow(),
            previous_status=previous_status,
            new_status=new_status,
            notes=notes,
            field_changes=field_changes,
            system_generated=system_generated,
            ip_address=user_info.get("ip_address") if user_info else None,
            user_agent=user_info.get("user_agent") if user_info else None
        )
        
        self.db.add(history)
        self.db.commit()
        self.db.refresh(history)
        
        return history
    
    def get_case_history(
        self,
        change_case_id: int
    ) -> List[models.ChangeHistory]:
        """Get complete history for a change case"""
        
        return self.db.query(models.ChangeHistory).filter(
            models.ChangeHistory.change_case_id == change_case_id
        ).order_by(models.ChangeHistory.action_at.asc()).all()


class NotificationService:
    """Service for sending change notifications"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def send_notification(
        self,
        notification_data: schemas.ChangeNotificationCreate
    ) -> models.ChangeNotification:
        """Send a notification and track delivery"""
        
        notification = models.ChangeNotification(
            change_case_id=notification_data.change_case_id,
            recipient_id=notification_data.recipient_id,
            recipient_email=notification_data.recipient_email,
            recipient_type=notification_data.recipient_type,
            notification_type=notification_data.notification_type,
            notification_method=notification_data.notification_method,
            subject=notification_data.subject,
            message=notification_data.message,
            delivered=False,
            opened=False,
            retry_count=0
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        # Send via notification service
        if config.CHANGE_NOTIFICATION_ENABLED:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{config.NOTIFICATION_SERVICE_URL}/notifications",
                        json={
                            "recipient_email": notification_data.recipient_email,
                            "subject": notification_data.subject,
                            "message": notification_data.message,
                            "notification_type": notification_data.notification_type
                        },
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        notification.delivered = True
                        notification.delivered_at = datetime.utcnow()
                        notification.sent_at = datetime.utcnow()
                    else:
                        notification.error = f"HTTP {response.status_code}"
                        
            except Exception as e:
                notification.error = str(e)
            
            self.db.commit()
            self.db.refresh(notification)
        
        return notification
    
    def notify_change_created(self, change_case: models.ChangeCase):
        """Notify relevant parties of new change"""
        # Implementation would create notification records
        pass
    
    def notify_change_approved(self, change_case: models.ChangeCase):
        """Notify relevant parties of approval"""
        pass
    
    def notify_change_rejected(self, change_case: models.ChangeCase):
        """Notify relevant parties of rejection"""
        pass
    
    def notify_change_implemented(self, change_case: models.ChangeCase):
        """Notify relevant parties of implementation"""
        pass


class AnalyticsService:
    """Service for change management analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_metrics(self) -> schemas.ChangeMetrics:
        """Get overall change metrics"""
        
        total = self.db.query(func.count(models.ChangeCase.id)).scalar() or 0
        
        status_counts = {
            "pending": self._count_by_status(models.ChangeStatus.PENDING),
            "under_review": self._count_by_status(models.ChangeStatus.UNDER_REVIEW),
            "approved": self._count_by_status(models.ChangeStatus.APPROVED),
            "rejected": self._count_by_status(models.ChangeStatus.REJECTED),
            "implemented": self._count_by_status(models.ChangeStatus.IMPLEMENTED),
            "cancelled": self._count_by_status(models.ChangeStatus.CANCELLED)
        }
        
        return schemas.ChangeMetrics(
            total_changes=total,
            pending_changes=status_counts["pending"],
            under_review_changes=status_counts["under_review"],
            approved_changes=status_counts["approved"],
            rejected_changes=status_counts["rejected"],
            implemented_changes=status_counts["implemented"],
            cancelled_changes=status_counts["cancelled"]
        )
    
    def _count_by_status(self, status: models.ChangeStatus) -> int:
        """Count cases by status"""
        return self.db.query(func.count(models.ChangeCase.id)).filter(
            models.ChangeCase.status == status
        ).scalar() or 0
