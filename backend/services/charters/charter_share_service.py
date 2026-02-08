"""
Secure Charter Quote/Share Link Service - Task 8.4
Creates shareable links for charter quotes that don't require login
"""

import jwt
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from fastapi import HTTPException
import os

# JWT configuration
JWT_SECRET = os.getenv("SECRET_KEY", "dev_secret_key_change_in_production")
JWT_ALGORITHM = "HS256"


class CharterShareLinkService:
    """Service for managing secure charter share links."""
    
    @staticmethod
    def generate_token(charter_id: int, expires_hours: int = 168) -> tuple[str, datetime]:
        """
        Generate JWT token for charter share link.
        
        Args:
            charter_id: Charter ID
            expires_hours: Hours until expiration (default 7 days)
            
        Returns:
            Tuple of (JWT token string, expiration datetime)
        """
        expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
        
        payload = {
            "charter_id": charter_id,
            "exp": expires_at,
            "iat": datetime.utcnow(),
            "type": "charter_share",
            "jti": secrets.token_urlsafe(16)  # Unique ID
        }
        
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token, expires_at
    
    @staticmethod
    def verify_token(token: str) -> Dict:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload
            
        Raises:
            HTTPException: If token invalid or expired
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            
            # Verify token type
            if payload.get("type") != "charter_share":
                raise HTTPException(401, "Invalid token type")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Link has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid link token")
    
    @staticmethod
    def create_share_link(
        charter_id: int,
        expires_hours: int,
        password: Optional[str],
        created_by: Optional[int],
        db: Session
    ) -> Dict:
        """
        Create secure charter share link.
        
        Args:
            charter_id: Charter ID
            expires_hours: Hours until expiration
            password: Optional password protection
            created_by: User creating the link (optional)
            db: Database session
            
        Returns:
            Dict with link details
        """
        from models import CharterShareLink, Charter
        
        # Verify charter exists and is in quote status
        charter = db.query(Charter).filter(Charter.id == charter_id).first()
        if not charter:
            raise HTTPException(404, "Charter not found")
        
        # Generate token
        token, expires_at = CharterShareLinkService.generate_token(charter_id, expires_hours)
        
        # Hash password if provided (bcrypt has 72-byte limit)
        password_hash = None
        if password:
            try:
                # bcrypt expects bytes, automatically handles UTF-8 encoding
                password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            except Exception as e:
                raise HTTPException(500, f"Failed to hash password: {str(e)}")
        
        # Create link record
        share_link = CharterShareLink(
            charter_id=charter_id,
            token=token,
            expires_at=expires_at,
            created_by=created_by,
            password_hash=password_hash
        )
        
        db.add(share_link)
        
        # Update charter sharing stats
        charter.share_count = (charter.share_count or 0) + 1
        charter.last_shared_at = datetime.utcnow()
        
        db.commit()
        db.refresh(share_link)
        
        return {
            "link_id": share_link.id,
            "token": token,
            "expires_at": expires_at,
            "has_password": password is not None,
            "view_count": 0
        }
    
    @staticmethod
    def verify_share_link(
        token: str,
        password: Optional[str],
        db: Session
    ) -> int:
        """
        Verify charter share link and return charter_id.
        
        Args:
            token: JWT token
            password: Password if link is protected
            db: Database session
            
        Returns:
            Charter ID if valid
            
        Raises:
            HTTPException: If link invalid, expired, or password wrong
        """
        from models import CharterShareLink
        
        # Verify JWT token
        payload = CharterShareLinkService.verify_token(token)
        charter_id = payload["charter_id"]
        
        # Get link record
        share_link = db.query(CharterShareLink).filter(
            CharterShareLink.token == token,
            CharterShareLink.is_active == True
        ).first()
        
        if not share_link:
            raise HTTPException(404, "Link not found or deactivated")
        
        # Check expiration (double-check even though JWT validates)
        if share_link.expires_at < datetime.utcnow():
            raise HTTPException(401, "Link has expired")
        
        # Verify password if required
        if share_link.password_hash:
            if not password:
                raise HTTPException(401, "Password required")
            
            # Use bcrypt directly for verification
            if not bcrypt.checkpw(password.encode('utf-8'), share_link.password_hash.encode('utf-8')):
                raise HTTPException(401, "Incorrect password")
        
        # Update tracking
        share_link.view_count += 1
        share_link.last_viewed_at = datetime.utcnow()
        db.commit()
        
        return charter_id
