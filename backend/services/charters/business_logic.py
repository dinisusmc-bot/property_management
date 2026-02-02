"""
Business logic for charter quote calculation
"""
from typing import Dict, Any
from models import Vehicle
from schemas import QuoteResponse
import config

class QuoteCalculator:
    """Calculate charter quotes based on business rules"""
    
    def __init__(self):
        self.minimum_deposit_pct = config.MINIMUM_DEPOSIT_PERCENTAGE / 100.0
        self.tax_rate = config.TAX_RATE / 100.0
        self.overnight_fee = config.OVERNIGHT_FEE
        self.weekend_fee_pct = config.WEEKEND_FEE_PERCENTAGE / 100.0
        self.gratuity_pct = config.GRATUITY_PERCENTAGE / 100.0
    
    def calculate_quote(
        self,
        vehicle: Vehicle,
        distance_miles: float,
        trip_hours: float,
        passengers: int,
        is_overnight: bool = False,
        is_weekend: bool = False
    ) -> QuoteResponse:
        """
        Calculate a quote for a charter
        
        Args:
            vehicle: Vehicle object with rates
            distance_miles: Total trip distance in miles
            trip_hours: Estimated trip duration in hours
            passengers: Number of passengers
            is_overnight: Whether trip includes overnight stay
            is_weekend: Whether trip is on weekend
        
        Returns:
            QuoteResponse with detailed pricing breakdown
        """
        # Base cost (minimum charge or hourly rate)
        hourly_rate = vehicle.base_rate
        base_cost = hourly_rate * trip_hours
        
        # Mileage cost
        mileage_cost = distance_miles * vehicle.per_mile_rate
        
        # Calculate subtotal before fees
        subtotal_before_fees = base_cost + mileage_cost
        
        # Overnight fee
        overnight_fee = self.overnight_fee if is_overnight else 0.0
        
        # Weekend surcharge (percentage of base + mileage)
        weekend_fee = subtotal_before_fees * self.weekend_fee_pct if is_weekend else 0.0
        
        # Driver gratuity (suggested, not required)
        driver_gratuity = subtotal_before_fees * self.gratuity_pct
        
        # Additional fees (toll estimates, parking, etc.)
        additional_fees = 0.0  # Can be customized based on route
        
        # Subtotal
        subtotal = (
            base_cost + 
            mileage_cost + 
            overnight_fee + 
            weekend_fee + 
            driver_gratuity + 
            additional_fees
        )
        
        # Tax
        tax = subtotal * self.tax_rate
        
        # Total cost
        total_cost = subtotal + tax
        
        # Deposit amount (minimum percentage)
        deposit_amount = total_cost * self.minimum_deposit_pct
        
        return QuoteResponse(
            vehicle_id=vehicle.id,
            vehicle_name=vehicle.name,
            distance_miles=round(distance_miles, 2),
            trip_hours=round(trip_hours, 2),
            passengers=passengers,
            base_cost=round(base_cost, 2),
            mileage_cost=round(mileage_cost, 2),
            overnight_fee=round(overnight_fee, 2),
            weekend_fee=round(weekend_fee, 2),
            driver_gratuity=round(driver_gratuity, 2),
            additional_fees=round(additional_fees, 2),
            subtotal=round(subtotal, 2),
            tax=round(tax, 2),
            total_cost=round(total_cost, 2),
            deposit_amount=round(deposit_amount, 2),
            deposit_percentage=round(self.minimum_deposit_pct * 100, 1)
        )
    
    def calculate_deposit(self, total_cost: float) -> float:
        """Calculate required deposit amount"""
        return round(total_cost * self.minimum_deposit_pct, 2)
    
    def calculate_balance(self, total_cost: float, amount_paid: float) -> float:
        """Calculate remaining balance"""
        return round(total_cost - amount_paid, 2)
