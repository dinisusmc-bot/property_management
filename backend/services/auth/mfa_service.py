"""
MFA (Multi-Factor Authentication) Service
Handles email-based 6-digit verification codes
"""
import secrets
import string
from passlib.hash import bcrypt
from typing import List, Tuple
from datetime import datetime, timedelta


def generate_mfa_code() -> str:
    """
    Generate a 6-digit verification code
    
    Returns:
        6-digit numeric code as string
    """
    return ''.join(secrets.choice(string.digits) for _ in range(6))


def verify_mfa_code(stored_code: str, provided_code: str, expiry_time: datetime) -> bool:
    """
    Verify MFA code
    
    Args:
        stored_code: The code that was sent to user
        provided_code: The code user entered
        expiry_time: When the code expires
        
    Returns:
        True if code is valid and not expired
    """
    if datetime.utcnow() > expiry_time:
        return False
    
    return stored_code == provided_code


def generate_backup_codes(count: int = 8) -> List[str]:
    """
    Generate backup codes
    
    Args:
        count: Number of backup codes to generate
        
    Returns:
        List of backup codes (format: XXXX-XXXX)
    """
    codes = []
    for _ in range(count):
        # Generate 8-character code in format XXXX-XXXX
        code = '-'.join([
            ''.join(secrets.choice('0123456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(4))
            for _ in range(2)
        ])
        codes.append(code)
    return codes


def hash_backup_codes(codes: List[str]) -> List[str]:
    """
    Hash backup codes for secure storage
    
    Args:
        codes: List of plain text backup codes
        
    Returns:
        List of hashed backup codes
    """
    return [bcrypt.hash(code) for code in codes]


def verify_backup_code(hashed_codes: List[str], code: str) -> Tuple[bool, int]:
    """
    Verify backup code against hashed list
    
    Args:
        hashed_codes: List of hashed backup codes
        code: Plain text backup code to verify
        
    Returns:
        Tuple of (is_valid, index_if_valid)
    """
    for idx, hashed in enumerate(hashed_codes):
        if bcrypt.verify(code, hashed):
            return True, idx
    return False, -1


def remove_used_backup_code(hashed_codes: List[str], index: int) -> List[str]:
    """
    Remove a used backup code from the list
    
    Args:
        hashed_codes: List of hashed backup codes
        index: Index of code to remove
        
    Returns:
        Updated list without the used code
    """
    return [code for i, code in enumerate(hashed_codes) if i != index]


def get_code_expiry_time(minutes: int = 10) -> datetime:
    """
    Get expiry time for a verification code
    
    Args:
        minutes: Number of minutes until expiry
        
    Returns:
        Expiry datetime
    """
    return datetime.utcnow() + timedelta(minutes=minutes)

