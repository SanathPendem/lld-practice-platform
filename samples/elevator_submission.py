"""
Sample Elevator Control System design
Demonstrates state modeling, dispatching, and separation between car and controller.
"""

from enum import Enum
from typing import List, Set, Optional


class ElevatorState(str, Enum):
    IDLE = "IDLE"
    MOVING_UP = "MOVING_UP"
    MOVING_DOWN = "MOVING_DOWN"
    DOOR_OPEN = "DOOR_OPEN"


class Floor:
    def __init__(self, level: int) -> None:
        self.level = level


class Request:
    def __init__(self, target_floor: int, is_internal: bool = True) -> None:
        self.target_floor = target_floor
        self.is_internal = is_internal


class ElevatorCar:
    def __init__(self, car_id: str, current_floor: int = 1) -> None:
        self.car_id = car_id
        self.current_floor = current_floor
        self.state = ElevatorState.IDLE
        self.destination_floors: Set[int] = set()

    def add_request(self, request: Request) -> None:
        self.destination_floors.add(request.target_floor)
        if self.state == ElevatorState.IDLE:
            self._update_state()

    def step(self) -> None:
        if not self.destination_floors:
            self.state = ElevatorState.IDLE
            return

        if self.state == ElevatorState.MOVING_UP:
            self.current_floor += 1
        elif self.state == ElevatorState.MOVING_DOWN:
            self.current_floor -= 1

        if self.current_floor in self.destination_floors:
            self.destination_floors.remove(self.current_floor)
            self.open_doors()

        self._update_state()

    def open_doors(self) -> None:
        self.state = ElevatorState.DOOR_OPEN

    def _update_state(self) -> None:
        if not self.destination_floors:
            self.state = ElevatorState.IDLE
        elif any(f > self.current_floor for f in self.destination_floors):
            self.state = ElevatorState.MOVING_UP
        elif any(f < self.current_floor for f in self.destination_floors):
            self.state = ElevatorState.MOVING_DOWN


class ElevatorController:
    """Coordinates dispatching requests among elevator cars."""

    def __init__(self, cars: List[ElevatorCar]) -> None:
        self.cars = cars

    def request_elevator(self, floor_level: int) -> ElevatorCar:
        chosen = min(
            self.cars,
            key=lambda c: abs(c.current_floor - floor_level) + len(c.destination_floors)
        )
        req = Request(target_floor=floor_level, is_internal=False)
        chosen.add_request(req)
        return chosen

    def step(self) -> None:
        for car in self.cars:
            car.step()
