"""
DOT Compliance Checking Utility

Federal Motor Carrier Safety Administration (FMCSA) regulations for driver service hours.
"""
from typing import Dict, List
from datetime import datetime, timedelta

# DOT Service Hour Limits (Hours of Service Regulations)
MAX_DRIVING_HOURS_DAY = 10  # Maximum driving hours in a single day
MAX_DUTY_HOURS_DAY = 15  # Maximum on-duty hours in a single day
MIN_REST_HOURS = 8  # Minimum consecutive off-duty hours required
MAX_DRIVING_HOURS_WEEK = 60  # Maximum driving hours in 7 consecutive days (non-commercial)
MAX_DUTY_HOURS_WEEK = 70  # Maximum duty hours in 8 consecutive days (commercial)


def calculate_estimated_hours(
    distance_miles: float,
    stops_count: int,
    trip_hours: float = None
) -> Dict[str, float]:
    """
    Estimate driving and duty hours based on distance, stops, and trip duration.
    
    Args:
        distance_miles: Total route distance in miles
        stops_count: Number of stops along the route
        trip_hours: Estimated trip duration (optional, calculated if not provided)
        
    Returns:
        Dict with estimated hours breakdown
    """
    # Average highway speed: 50 mph
    # City/local speed: 25 mph
    # Use average of 40 mph for charter routes
    calculated_driving_hours = distance_miles / 40.0
    
    # Add time for stops (15 minutes per stop for passenger boarding/unloading)
    stop_time_hours = (stops_count * 15) / 60.0
    
    # Add pre-trip inspection time (30 minutes minimum)
    inspection_hours = 0.5
    
    # Add post-trip procedures (15 minutes)
    post_trip_hours = 0.25
    
    # If trip_hours provided, use it as driving time, otherwise use calculated
    driving_hours = trip_hours if trip_hours else calculated_driving_hours
    
    # Total duty hours = driving + stops + inspections + procedures
    duty_hours = driving_hours + stop_time_hours + inspection_hours + post_trip_hours
    
    return {
        "driving_hours": round(driving_hours, 2),
        "stop_time_hours": round(stop_time_hours, 2),
        "inspection_hours": round(inspection_hours, 2),
        "post_trip_hours": round(post_trip_hours, 2),
        "total_duty_hours": round(duty_hours, 2),
        "calculated_from_distance": trip_hours is None
    }


def check_dot_compliance(
    distance_miles: float,
    stops_count: int = 0,
    trip_hours: float = None,
    is_multi_day: bool = False,
    driver_hours_this_week: float = 0
) -> Dict:
    """
    Check if a charter trip complies with DOT Hours of Service regulations.
    
    Args:
        distance_miles: Total route distance in miles
        stops_count: Number of stops
        trip_hours: Estimated trip duration (optional)
        is_multi_day: Whether trip spans multiple days
        driver_hours_this_week: Driver's hours already worked this week
        
    Returns:
        Dict with compliance status and details
    """
    # Calculate estimated hours
    hours = calculate_estimated_hours(distance_miles, stops_count, trip_hours)
    
    driving_hours = hours["driving_hours"]
    duty_hours = hours["total_duty_hours"]
    
    # Initialize compliance results
    compliance = {
        "compliant": True,
        "violations": [],
        "warnings": [],
        "estimated_hours": hours,
        "requires_second_driver": False,
        "max_daily_driving": MAX_DRIVING_HOURS_DAY,
        "max_daily_duty": MAX_DUTY_HOURS_DAY
    }
    
    # Check daily driving hour limit
    if driving_hours > MAX_DRIVING_HOURS_DAY:
        compliance["compliant"] = False
        compliance["violations"].append(
            f"Driving hours ({driving_hours:.1f}h) exceed daily limit ({MAX_DRIVING_HOURS_DAY}h)"
        )
        compliance["requires_second_driver"] = True
    elif driving_hours > MAX_DRIVING_HOURS_DAY * 0.9:  # Within 90% of limit
        compliance["warnings"].append(
            f"Driving hours ({driving_hours:.1f}h) approaching daily limit ({MAX_DRIVING_HOURS_DAY}h)"
        )
    
    # Check daily duty hour limit
    if duty_hours > MAX_DUTY_HOURS_DAY:
        compliance["compliant"] = False
        compliance["violations"].append(
            f"Duty hours ({duty_hours:.1f}h) exceed daily limit ({MAX_DUTY_HOURS_DAY}h)"
        )
        compliance["requires_second_driver"] = True
    elif duty_hours > MAX_DUTY_HOURS_DAY * 0.9:
        compliance["warnings"].append(
            f"Duty hours ({duty_hours:.1f}h) approaching daily limit ({MAX_DUTY_HOURS_DAY}h)"
        )
    
    # Check weekly hours if provided
    if driver_hours_this_week > 0:
        projected_weekly_hours = driver_hours_this_week + duty_hours
        
        if projected_weekly_hours > MAX_DUTY_HOURS_WEEK:
            compliance["compliant"] = False
            compliance["violations"].append(
                f"Weekly duty hours ({projected_weekly_hours:.1f}h) would exceed limit ({MAX_DUTY_HOURS_WEEK}h)"
            )
        elif projected_weekly_hours > MAX_DUTY_HOURS_WEEK * 0.9:
            compliance["warnings"].append(
                f"Weekly duty hours ({projected_weekly_hours:.1f}h) approaching limit ({MAX_DUTY_HOURS_WEEK}h)"
            )
    
    # Multi-day trip considerations
    if is_multi_day:
        if duty_hours < MIN_REST_HOURS:
            compliance["warnings"].append(
                f"Driver must have {MIN_REST_HOURS} consecutive hours of rest between duty periods"
            )
    
    # Recommendation for second driver
    if driving_hours > 8 or duty_hours > 12:
        compliance["warnings"].append(
            "Consider assigning a second driver for comfort and flexibility"
        )
    
    # Calculate recommended rest time
    if duty_hours > 0:
        compliance["minimum_rest_required_hours"] = MIN_REST_HOURS
        compliance["earliest_next_trip"] = "8 hours after trip completion"
    
    return compliance


def get_compliance_recommendation(distance_miles: float, trip_hours: float = None) -> str:
    """
    Get a simple compliance recommendation for a trip.
    
    Args:
        distance_miles: Total route distance in miles
        trip_hours: Estimated trip duration
        
    Returns:
        String recommendation
    """
    result = check_dot_compliance(distance_miles, 0, trip_hours)
    
    if not result["compliant"]:
        return "NON_COMPLIANT - Requires second driver or trip modification"
    elif result["warnings"]:
        return "COMPLIANT_WITH_WARNINGS - Consider second driver for safety margin"
    else:
        return "COMPLIANT - Single driver sufficient"


def suggest_second_driver_split(total_hours: float) -> Dict:
    """
    Suggest how to split driving hours between two drivers.
    
    Args:
        total_hours: Total trip hours
        
    Returns:
        Dict with driver split recommendation
    """
    if total_hours <= MAX_DRIVING_HOURS_DAY:
        return {
            "second_driver_needed": False,
            "message": "Single driver sufficient for this trip"
        }
    
    # Split evenly between drivers
    hours_per_driver = total_hours / 2
    
    # Add buffer time for driver switches (30 min per switch)
    num_switches = max(1, int(total_hours / 4))  # Switch every ~4 hours
    switch_time = (num_switches * 0.5)
    
    adjusted_trip_time = total_hours + switch_time
    
    return {
        "second_driver_needed": True,
        "hours_per_driver": round(hours_per_driver, 2),
        "number_of_driver_switches": num_switches,
        "switch_buffer_time_hours": round(switch_time, 2),
        "adjusted_total_trip_time": round(adjusted_trip_time, 2),
        "recommendation": f"Split driving between two drivers, switching every {4} hours"
    }
