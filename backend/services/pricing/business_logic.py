"""
Business logic for Pricing Service
"""
from sqlalchemy.orm import Session
from models import PricingRule, QuoteCalculation, PriceHistory, RuleType, RuleScope
from schemas import QuoteRequest, QuoteBreakdown
import config
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)


class PricingEngine:
    """Main pricing calculation engine"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_quote(self, request: QuoteRequest) -> Dict:
        """
        Calculate quote based on request and applicable pricing rules
        
        Args:
            request: QuoteRequest with trip details
            
        Returns:
            Dict with calculation breakdown
        """
        logger.info(f"Calculating quote for client {request.client_id}, vehicle {request.vehicle_id}")
        
        # Get applicable rules
        rules = self._get_applicable_rules(request)
        logger.info(f"Found {len(rules)} applicable pricing rules")
        
        # Initialize costs
        base_cost = 0.0
        mileage_cost = 0.0
        time_based_cost = 0.0
        
        # Apply rules by priority
        rules_applied = []
        for rule in rules:
            if rule.rule_type == RuleType.BASE_RATE and rule.base_rate:
                base_cost = max(base_cost, rule.base_rate)
                rules_applied.append(rule.id)
                logger.info(f"Applied base rate rule {rule.id}: ${rule.base_rate}")
            
            elif rule.rule_type == RuleType.MILEAGE_RATE and rule.per_mile_rate:
                mileage_cost = request.total_miles * rule.per_mile_rate
                rules_applied.append(rule.id)
                logger.info(f"Applied mileage rate rule {rule.id}: {request.total_miles} miles * ${rule.per_mile_rate}")
            
            elif rule.rule_type == RuleType.TIME_MULTIPLIER and rule.per_hour_rate:
                time_based_cost = request.trip_hours * rule.per_hour_rate
                rules_applied.append(rule.id)
                logger.info(f"Applied time-based rule {rule.id}: {request.trip_hours} hours * ${rule.per_hour_rate}")
        
        # If no rules matched, use defaults
        if base_cost == 0.0:
            base_cost = config.DEFAULT_BASE_RATE
            logger.info(f"Using default base rate: ${base_cost}")
        
        if mileage_cost == 0.0 and request.total_miles > 0:
            mileage_cost = request.total_miles * config.DEFAULT_PER_MILE_RATE
            logger.info(f"Using default mileage rate: {request.total_miles} * ${config.DEFAULT_PER_MILE_RATE}")
        
        # Calculate subtotal before multipliers
        subtotal = base_cost + mileage_cost + time_based_cost
        
        # Apply multipliers
        multipliers = self._calculate_multipliers(request, rules)
        
        # Apply multipliers to subtotal
        adjusted_subtotal = subtotal
        adjusted_subtotal *= multipliers['weekend_multiplier']
        adjusted_subtotal *= multipliers['overnight_multiplier']
        adjusted_subtotal *= multipliers['holiday_multiplier']
        adjusted_subtotal *= multipliers['seasonal_multiplier']
        
        # Add additional fees
        fuel_surcharge = self._calculate_fuel_surcharge(request.total_miles)
        total_cost = adjusted_subtotal + request.additional_fees + fuel_surcharge
        
        # Apply min/max constraints from rules
        for rule in rules:
            if rule.min_charge and total_cost < rule.min_charge:
                logger.info(f"Applying minimum charge from rule {rule.id}: ${rule.min_charge}")
                total_cost = rule.min_charge
            if rule.max_charge and total_cost > rule.max_charge:
                logger.info(f"Applying maximum charge from rule {rule.id}: ${rule.max_charge}")
                total_cost = rule.max_charge
        
        # Build calculation notes
        notes = self._build_calculation_notes(rules, multipliers)
        
        breakdown = QuoteBreakdown(
            base_cost=base_cost,
            mileage_cost=mileage_cost,
            time_based_cost=time_based_cost,
            weekend_multiplier=multipliers['weekend_multiplier'],
            overnight_multiplier=multipliers['overnight_multiplier'],
            holiday_multiplier=multipliers['holiday_multiplier'],
            seasonal_multiplier=multipliers['seasonal_multiplier'],
            additional_fees=request.additional_fees,
            fuel_surcharge=fuel_surcharge,
            subtotal=subtotal,
            total_cost=round(total_cost, 2),
            rules_applied=rules_applied,
            calculation_notes=notes
        )
        
        logger.info(f"Quote calculated: ${total_cost:.2f}")
        
        return {
            "breakdown": breakdown,
            "rules_applied_ids": rules_applied
        }
    
    def _get_applicable_rules(self, request: QuoteRequest) -> List[PricingRule]:
        """Get all applicable pricing rules for the request"""
        query = self.db.query(PricingRule).filter(
            PricingRule.is_active == True
        )
        
        # Filter by date range
        query = query.filter(
            (PricingRule.effective_from == None) | (PricingRule.effective_from <= request.trip_date),
            (PricingRule.effective_to == None) | (PricingRule.effective_to >= request.trip_date)
        )
        
        # Get all potential rules
        all_rules = query.all()
        
        # Filter by scope and specific conditions
        applicable_rules = []
        for rule in all_rules:
            # Check scope
            if rule.scope == RuleScope.CLIENT and rule.client_id != request.client_id:
                continue
            if rule.scope == RuleScope.VEHICLE and rule.vehicle_id != request.vehicle_id:
                continue
            
            # Check time conditions
            if rule.is_overnight and not request.is_overnight:
                continue
            if rule.is_weekend and not request.is_weekend:
                continue
            if rule.is_holiday and not request.is_holiday:
                continue
            
            applicable_rules.append(rule)
        
        # Sort by priority (highest first)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        return applicable_rules
    
    def _calculate_multipliers(self, request: QuoteRequest, rules: List[PricingRule]) -> Dict[str, float]:
        """Calculate all applicable multipliers"""
        multipliers = {
            'weekend_multiplier': 1.0,
            'overnight_multiplier': 1.0,
            'holiday_multiplier': 1.0,
            'seasonal_multiplier': 1.0
        }
        
        # Check for specific multiplier rules
        for rule in rules:
            if rule.rule_type == RuleType.TIME_MULTIPLIER:
                if rule.is_weekend and request.is_weekend:
                    multipliers['weekend_multiplier'] = max(multipliers['weekend_multiplier'], rule.multiplier)
                if rule.is_overnight and request.is_overnight:
                    multipliers['overnight_multiplier'] = max(multipliers['overnight_multiplier'], rule.multiplier)
                if rule.is_holiday and request.is_holiday:
                    multipliers['holiday_multiplier'] = max(multipliers['holiday_multiplier'], rule.multiplier)
            
            elif rule.rule_type == RuleType.SEASONAL:
                multipliers['seasonal_multiplier'] = max(multipliers['seasonal_multiplier'], rule.multiplier)
        
        # Apply defaults if no rules specified
        if multipliers['weekend_multiplier'] == 1.0 and request.is_weekend:
            multipliers['weekend_multiplier'] = config.WEEKEND_MULTIPLIER
        
        if multipliers['overnight_multiplier'] == 1.0 and request.is_overnight:
            multipliers['overnight_multiplier'] = config.OVERNIGHT_MULTIPLIER
        
        if multipliers['holiday_multiplier'] == 1.0 and request.is_holiday:
            multipliers['holiday_multiplier'] = config.HOLIDAY_MULTIPLIER
        
        return multipliers
    
    def _calculate_fuel_surcharge(self, miles: float) -> float:
        """Calculate fuel surcharge based on miles"""
        # Simple calculation: $0.50 per 50 miles
        if miles > 50:
            return round((miles / 50) * 0.50, 2)
        return 0.0
    
    def _build_calculation_notes(self, rules: List[PricingRule], multipliers: Dict) -> str:
        """Build human-readable calculation notes"""
        notes = []
        
        if len(rules) > 0:
            notes.append(f"Applied {len(rules)} pricing rule(s)")
        else:
            notes.append("Used default pricing (no specific rules matched)")
        
        if multipliers['weekend_multiplier'] > 1.0:
            notes.append(f"Weekend surcharge: {(multipliers['weekend_multiplier']-1)*100:.0f}%")
        
        if multipliers['overnight_multiplier'] > 1.0:
            notes.append(f"Overnight surcharge: {(multipliers['overnight_multiplier']-1)*100:.0f}%")
        
        if multipliers['holiday_multiplier'] > 1.0:
            notes.append(f"Holiday surcharge: {(multipliers['holiday_multiplier']-1)*100:.0f}%")
        
        if multipliers['seasonal_multiplier'] > 1.0:
            notes.append(f"Peak season surcharge: {(multipliers['seasonal_multiplier']-1)*100:.0f}%")
        
        return "; ".join(notes)
    
    def save_quote_calculation(
        self,
        request: QuoteRequest,
        breakdown: QuoteBreakdown,
        rules_applied_ids: List[int],
        charter_id: Optional[int] = None
    ) -> QuoteCalculation:
        """Save quote calculation to database"""
        
        # Calculate expiration (30 days from now)
        expires_at = datetime.utcnow() + timedelta(days=30)
        
        calculation = QuoteCalculation(
            charter_id=charter_id,
            client_id=request.client_id,
            vehicle_id=request.vehicle_id,
            trip_date=request.trip_date,
            passengers=request.passengers,
            total_miles=request.total_miles,
            trip_hours=request.trip_hours,
            is_overnight=request.is_overnight,
            is_weekend=request.is_weekend,
            is_holiday=request.is_holiday,
            base_cost=breakdown.base_cost,
            mileage_cost=breakdown.mileage_cost,
            time_based_cost=breakdown.time_based_cost,
            weekend_multiplier=breakdown.weekend_multiplier,
            overnight_multiplier=breakdown.overnight_multiplier,
            holiday_multiplier=breakdown.holiday_multiplier,
            seasonal_multiplier=breakdown.seasonal_multiplier,
            additional_fees=breakdown.additional_fees,
            fuel_surcharge=breakdown.fuel_surcharge,
            subtotal=breakdown.subtotal,
            total_cost=breakdown.total_cost,
            rules_applied=json.dumps(rules_applied_ids),
            calculation_notes=breakdown.calculation_notes,
            expires_at=expires_at,
            status="draft"
        )
        
        self.db.add(calculation)
        self.db.commit()
        self.db.refresh(calculation)
        
        logger.info(f"Saved quote calculation {calculation.id}")
        
        return calculation


class MultiVehiclePricingEngine:
    """Multi-vehicle pricing calculation engine - Task 8.3"""
    
    @staticmethod
    def calculate_multi_vehicle_pricing(
        total_passengers: int,
        total_miles: float,
        vehicle_count: int,
        vehicle_type: str,
        estimated_hours: float,
        base_rate_per_mile: float = None,
        base_rate_per_hour: float = None
    ) -> Dict:
        """
        Calculate pricing for multi-vehicle charter.
        
        Args:
            total_passengers: Total passenger count
            total_miles: Total miles for trip
            vehicle_count: Number of vehicles needed
            vehicle_type: Type of vehicle (e.g., "56_passenger")
            estimated_hours: Estimated trip duration in hours
            base_rate_per_mile: Override base rate per mile (optional)
            base_rate_per_hour: Override base rate per hour (optional)
            
        Returns:
            Dict with pricing breakdown per vehicle and total
        """
        # Use config defaults if not provided
        if base_rate_per_mile is None:
            base_rate_per_mile = config.BASE_RATE_PER_MILE
        if base_rate_per_hour is None:
            base_rate_per_hour = config.BASE_RATE_PER_HOUR
        
        # Calculate passengers per vehicle (distribute evenly)
        passengers_per_vehicle = total_passengers // vehicle_count
        remaining_passengers = total_passengers % vehicle_count
        
        # Calculate miles per vehicle (same for all vehicles)
        miles_per_vehicle = total_miles
        
        # Calculate base cost per vehicle
        mileage_cost_per_vehicle = miles_per_vehicle * base_rate_per_mile
        hourly_cost_per_vehicle = estimated_hours * base_rate_per_hour
        base_cost_per_vehicle = mileage_cost_per_vehicle + hourly_cost_per_vehicle
        
        # Total base cost
        total_base_cost = base_cost_per_vehicle * vehicle_count
        
        # NOTE: No bulk discount applied per user requirement
        # Each vehicle priced independently
        
        # Build vehicle breakdown
        vehicles = []
        for i in range(vehicle_count):
            # Distribute remaining passengers to first vehicles
            vehicle_passengers = passengers_per_vehicle + (1 if i < remaining_passengers else 0)
            
            vehicles.append({
                "vehicle_number": i + 1,
                "passengers": vehicle_passengers,
                "miles": miles_per_vehicle,
                "estimated_hours": estimated_hours,
                "mileage_cost": round(mileage_cost_per_vehicle, 2),
                "hourly_cost": round(hourly_cost_per_vehicle, 2),
                "total_cost": round(base_cost_per_vehicle, 2)
            })
        
        return {
            "vehicle_count": vehicle_count,
            "vehicle_type": vehicle_type,
            "total_passengers": total_passengers,
            "passengers_per_vehicle": passengers_per_vehicle,
            "remaining_passengers": remaining_passengers,
            "total_miles": miles_per_vehicle,
            "estimated_hours": estimated_hours,
            "base_rate_per_mile": base_rate_per_mile,
            "base_rate_per_hour": base_rate_per_hour,
            "mileage_cost_per_vehicle": round(mileage_cost_per_vehicle, 2),
            "hourly_cost_per_vehicle": round(hourly_cost_per_vehicle, 2),
            "base_cost_per_vehicle": round(base_cost_per_vehicle, 2),
            "total_base_cost": round(total_base_cost, 2),
            "vehicles": vehicles,
            "notes": "No bulk discount applied. Each vehicle priced independently."
        }
