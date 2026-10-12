"""
Attempt 1 (Naive): Parking Lot
Characteristics:
- God class anti-pattern: ParkingLot contains 9 methods doing everything from pricing to thermal printing
- Missing domain entity: No ParkingTicket entity
- Hardcoded pricing: No PricingStrategy interface or class
"""

from enum import Enum
from typing import List, Dict, Optional
import time

class VehicleType(Enum):
    MOTORCYCLE = 1
    CAR = 2
    TRUCK = 3

class Vehicle:
    def __init__(self, license_plate: str, vehicle_type: VehicleType):
        self.license_plate = license_plate
        self.vehicle_type = vehicle_type

class ParkingSpot:
    def __init__(self, spot_id: str, spot_type: VehicleType):
        self.spot_id = spot_id
        self.spot_type = spot_type
        self.is_occupied = False
        self.parked_vehicle: Optional[Vehicle] = None

class ParkingLot:
    """God class that attempts to manage spots, tickets, gates, printing, and billing."""
    def __init__(self, lot_id: str):
        self.lot_id = lot_id
        self.spots: List[ParkingSpot] = []
        self.active_parkings: Dict[str, float] = {}

    def park_vehicle(self, vehicle: Vehicle) -> Optional[str]:
        for spot in self.spots:
            if not spot.is_occupied and spot.spot_type == vehicle.vehicle_type:
                spot.is_occupied = True
                spot.parked_vehicle = vehicle
                self.active_parkings[vehicle.license_plate] = time.time()
                return spot.spot_id
        return None

    def unpark_vehicle(self, license_plate: str) -> bool:
        for spot in self.spots:
            if spot.parked_vehicle and spot.parked_vehicle.license_plate == license_plate:
                spot.is_occupied = False
                spot.parked_vehicle = None
                return True
        return False

    def is_available(self, v_type: VehicleType) -> bool:
        return any(s.spot_type == v_type and not s.is_occupied for s in self.spots)

    def calculate_fee(self, license_plate: str, hours: float) -> float:
        # Hardcoded pricing logic directly inside the parking lot
        return hours * 10.0

    def scan_license_plate(self, plate: str) -> bool:
        return len(plate) > 3

    def print_thermal_receipt(self, license_plate: str, amount: float) -> str:
        return f"Receipt for {license_plate}: ${amount}"

    def open_entry_barrier(self) -> None:
        pass

    def close_entry_barrier(self) -> None:
        pass

    def trigger_emergency_alarm(self) -> None:
        pass
