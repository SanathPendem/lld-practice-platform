from typing import List, Dict, Optional
from lld_platform.domain.models import Problem, EvaluationSpec


def get_seed_problems() -> List[Problem]:
    return [
        Problem(
            id="parking-lot",
            title="Design a Multi-Floor Parking Lot",
            difficulty="Medium",
            summary="Model a multi-level parking lot supporting various vehicle types, automated spot assignment, and flexible pricing calculation.",
            requirements=[
                "Support multiple vehicle types: Motorcycle, Car, and Truck.",
                "Support parking spots corresponding to vehicle sizes (Compact, Large, Motorcycle).",
                "Assign tickets upon vehicle entry with timestamp and assigned spot.",
                "Calculate parking fees at exit based on duration and vehicle type using a flexible strategy.",
                "Support checking available spots per floor and in total.",
                "Prevent parking when full or when no suitable spot size exists."
            ],
            scope_boundaries=[
                "Out of scope: Payment gateway processing (assume simple pay/settle callback).",
                "Out of scope: Physical sensor/IoT hardware integration.",
                "Focus on: Class boundaries, Spot assignment logic, Ticket lifecycle, and Strategy pattern for fee calculation."
            ],
            evaluation_spec=EvaluationSpec(
                required_entities=["Vehicle", "ParkingSpot", "ParkingLot", "ParkingTicket", "PricingStrategy"],
                required_operations=["park_vehicle", "unpark_vehicle", "calculate_fee", "is_available"],
                god_class_method_threshold=7,
                expected_relationships={
                    "ParkingLot": ["ParkingSpot", "ParkingTicket"],
                    "ParkingTicket": ["Vehicle", "ParkingSpot"],
                },
                key_design_patterns=["Strategy Pattern (Pricing)", "Factory/Builder Pattern (Spot assignment or vehicle creation)"],
            ),
        ),
        Problem(
            id="elevator-system",
            title="Design an Elevator Control System",
            difficulty="Hard",
            summary="Model an elevator system managing multiple elevator cars across floors, handling internal cabin and external hall requests safely.",
            requirements=[
                "Manage multiple elevator cars operating across N floors.",
                "Support elevator states: IDLE, MOVING_UP, MOVING_DOWN, and DOOR_OPEN.",
                "Handle internal requests (passenger selects floor inside elevator) and external requests (hall call up/down).",
                "Implement an extensible dispatching mechanism to route requests to the most appropriate elevator car.",
                "Step simulation / movement logic to advance elevator positions and process pending stops."
            ],
            scope_boundaries=[
                "Out of scope: Motor voltage physics and cable tension models.",
                "Out of scope: Weight sensor calibrations and emergency fire alarms.",
                "Focus on: State management, separation between ElevatorCar, Dispatcher/Controller, and Request models."
            ],
            evaluation_spec=EvaluationSpec(
                required_entities=["ElevatorCar", "ElevatorController", "Floor", "Request", "ElevatorState"],
                required_operations=["request_elevator", "step", "open_doors", "add_request"],
                god_class_method_threshold=8,
                expected_relationships={
                    "ElevatorController": ["ElevatorCar", "Request"],
                },
                key_design_patterns=["State Pattern (Elevator movement/doors)", "Strategy Pattern (Dispatching algorithm)"],
            ),
        ),
        Problem(
            id="splitwise-expenses",
            title="Design Splitwise (Expense Sharing App)",
            difficulty="Medium",
            summary="Model a group expense management tool allowing users to record shared payments and split debts using different split algorithms.",
            requirements=[
                "Allow users to register and form groups.",
                "Record expenses paid by one user on behalf of others.",
                "Support multiple split strategies: Equal split, Exact amounts, and Percentage split.",
                "Track bilateral balances between users.",
                "Support viewing net balances and settling debts between two users."
            ],
            scope_boundaries=[
                "Out of scope: Banking rails, ACH transfers, currency exchange rate fluctuations.",
                "Focus on: Split strategy polymorphism, Expense immutability, and Balance calculation separation."
            ],
            evaluation_spec=EvaluationSpec(
                required_entities=["User", "Expense", "SplitStrategy", "Group"],
                required_operations=["add_expense", "calculate_splits", "get_balance", "settle_debt"],
                god_class_method_threshold=7,
                expected_relationships={
                    "Group": ["User", "Expense"],
                    "Expense": ["User", "SplitStrategy"],
                },
                key_design_patterns=["Strategy Pattern (Split calculation)", "Factory Pattern (Expense creation)"],
            ),
        ),
        Problem(
            id="in-memory-cache",
            title="Design an In-Memory Cache with Eviction",
            difficulty="Easy-Medium",
            summary="Model a generic key-value store with configurable capacity and pluggable eviction policies (such as LRU or LFU).",
            requirements=[
                "Store key-value pairs with fast lookup and retrieval.",
                "Enforce a maximum storage capacity.",
                "Evict entries when full according to a pluggable eviction strategy (e.g. Least Recently Used).",
                "Notify or track cache hits and misses.",
                "Support clear and size inspection operations."
            ],
            scope_boundaries=[
                "Out of scope: Multi-node distributed hash rings or Redis-style network protocol.",
                "Focus on: Clean separation between Cache storage and EvictionPolicy strategy."
            ],
            evaluation_spec=EvaluationSpec(
                required_entities=["Cache", "EvictionPolicy", "CacheEntry"],
                required_operations=["get", "put", "evict", "size"],
                god_class_method_threshold=6,
                expected_relationships={
                    "Cache": ["EvictionPolicy", "CacheEntry"],
                },
                key_design_patterns=["Strategy Pattern (Eviction Policy)"],
            ),
        ),
    ]


class Catalog:
    def __init__(self, problems: Optional[List[Problem]] = None):
        self._problems: Dict[str, Problem] = {
            p.id: p for p in (problems or get_seed_problems())
        }

    def get(self, problem_id: str) -> Optional[Problem]:
        return self._problems.get(problem_id)

    def list_all(self) -> List[Problem]:
        return list(self._problems.values())
