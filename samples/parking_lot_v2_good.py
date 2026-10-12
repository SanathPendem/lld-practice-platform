"""
Attempt 2 (Refactored): Parking Lot
Improvements:
- Introduced ParkingTicket entity with timestamps and spot association
- Extracted PricingStrategy interface and HourlyPricingStrategy (Open/Closed Principle)
- ParkingLot decomposes concerns and maintains focused public API under threshold
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Dict
from datetime import datetime, timezone
import uuid


class VehicleType(str, Enum):
    MOTORCYCLE = "MOTORCYCLE"
    CAR = "CAR"
    TRUCK = "TRUCK"


class Vehicle:
    def __init__(self, license_plate: str, vehicle_type: VehicleType) -> None:
        self.license_plate = license_plate
        self.vehicle_type = vehicle_type


class ParkingSpot:
    def __init__(self, spot_id: str, spot_type: VehicleType) -> None:
        self.spot_id = spot_id
        self.spot_type = spot_type
        self.parked_vehicle: Optional[Vehicle] = None

    @property
    def is_occupied(self) -> bool:
        return self.parked_vehicle is not None

    def assign_vehicle(self, vehicle: Vehicle) -> bool:
        if self.is_occupied or vehicle.vehicle_type != self.spot_type:
            return False
        self.parked_vehicle = vehicle
        return True

    def vacate(self) -> Optional[Vehicle]:
        v = self.parked_vehicle
        self.parked_vehicle = None
        return v


class ParkingTicket:
    def __init__(self, ticket_id: str, vehicle: Vehicle, spot: ParkingSpot) -> None:
        self.ticket_id = ticket_id
        self.vehicle = vehicle
        self.spot = spot
        self.issued_at: datetime = datetime.now(timezone.utc)
        self.paid_at: Optional[datetime] = None


class PricingStrategy(ABC):
    @abstractmethod
    def calculate_fee(self, ticket: ParkingTicket, duration_hours: float) -> float:
        pass


class HourlyPricingStrategy(PricingStrategy):
    RATES = {
        VehicleType.MOTORCYCLE: 2.0,
        VehicleType.CAR: 5.0,
        VehicleType.TRUCK: 10.0,
    }

    def calculate_fee(self, ticket: ParkingTicket, duration_hours: float) -> float:
        rate = self.RATES.get(ticket.vehicle.vehicle_type, 5.0)
        return max(1.0, duration_hours) * rate


class ParkingLot:
    """Coordinating entity managing spots, ticket issuance, and fee dispatch."""

    def __init__(self, name: str, pricing_strategy: PricingStrategy) -> None:
        self.name = name
        self.spots: List[ParkingSpot] = []
        self.active_tickets: Dict[str, ParkingTicket] = {}
        self.pricing_strategy = pricing_strategy

    def add_spot(self, spot: ParkingSpot) -> None:
        self.spots.append(spot)

    def is_available(self, v_type: VehicleType) -> bool:
        return any(not s.is_occupied and s.spot_type == v_type for s in self.spots)

    def park_vehicle(self, vehicle: Vehicle) -> Optional[ParkingTicket]:
        for spot in self.spots:
            if spot.assign_vehicle(vehicle):
                ticket = ParkingTicket(
                    ticket_id=f"tkt_{uuid.uuid4().hex[:6]}",
                    vehicle=vehicle,
                    spot=spot,
                )
                self.active_tickets[ticket.ticket_id] = ticket
                return ticket
        return None

    def unpark_vehicle(self, ticket_id: str) -> Optional[Vehicle]:
        ticket = self.active_tickets.pop(ticket_id, None)
        if not ticket:
            return None
        return ticket.spot.vacate()

    def calculate_fee(self, ticket_id: str, duration_hours: float) -> float:
        ticket = self.active_tickets.get(ticket_id)
        if not ticket:
            raise KeyError(f"Ticket {ticket_id} not found.")
        return self.pricing_strategy.calculate_fee(ticket, duration_hours)
