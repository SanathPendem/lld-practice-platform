import unittest
from lld_platform.domain.models import Submission
from lld_platform.domain.feedback import CheckSeverity
from lld_platform.problems.catalog import Catalog
from lld_platform.evaluation.deterministic import DeterministicEvaluator


class TestDeterministicEvaluator(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = Catalog()
        self.parking_problem = self.catalog.get("parking-lot")
        self.assertIsNotNone(self.parking_problem)
        self.evaluator = DeterministicEvaluator()

    def test_syntax_error_detection(self) -> None:
        invalid_code = "class ParkingLot def broken syntax:"
        submission = Submission(code=invalid_code)
        result = self.evaluator.evaluate(submission, self.parking_problem)

        self.assertFalse(result.passed)
        self.assertEqual(result.score, 0)
        syntax_findings = [f for f in result.findings if f.rule_name == "syntax_validity"]
        self.assertTrue(len(syntax_findings) > 0)
        self.assertFalse(syntax_findings[0].passed)
        self.assertIsNotNone(syntax_findings[0].line_reference)

    def test_missing_required_entities(self) -> None:
        # Code only has Vehicle, missing ParkingSpot, ParkingLot, ParkingTicket, PricingStrategy
        partial_code = """
class Vehicle:
    def __init__(self, plate: str):
        self.plate = plate
"""
        submission = Submission(code=partial_code)
        result = self.evaluator.evaluate(submission, self.parking_problem)

        self.assertFalse(result.passed)
        missing_entities = [
            f.target_entity for f in result.findings
            if f.rule_name == "required_entities" and not f.passed
        ]
        self.assertIn("ParkingSpot", missing_entities)
        self.assertIn("ParkingTicket", missing_entities)
        self.assertIn("PricingStrategy", missing_entities)

    def test_god_class_detection(self) -> None:
        # A class with 9 methods exceeding threshold 7
        god_class_code = """
class Vehicle: pass
class ParkingSpot: pass
class ParkingTicket: pass
class PricingStrategy: pass

class ParkingLot:
    def m1(self): pass
    def m2(self): pass
    def m3(self): pass
    def m4(self): pass
    def m5(self): pass
    def m6(self): pass
    def m7(self): pass
    def m8(self): pass
    def m9(self): pass
    def park_vehicle(self): pass
    def unpark_vehicle(self): pass
    def calculate_fee(self): pass
    def is_available(self): pass
"""
        submission = Submission(code=god_class_code)
        result = self.evaluator.evaluate(submission, self.parking_problem)

        god_findings = [
            f for f in result.findings
            if f.rule_name == "single_responsibility_god_class" and not f.passed
        ]
        self.assertEqual(len(god_findings), 1)
        self.assertEqual(god_findings[0].target_entity, "ParkingLot")
        self.assertEqual(god_findings[0].severity, CheckSeverity.WARNING)
        self.assertIn("Decompose 'ParkingLot'", god_findings[0].suggestion)

    def test_missing_required_operations(self) -> None:
        code_without_ops = """
class Vehicle: pass
class ParkingSpot: pass
class ParkingLot: pass
class ParkingTicket: pass
class PricingStrategy: pass
"""
        submission = Submission(code=code_without_ops)
        result = self.evaluator.evaluate(submission, self.parking_problem)

        missing_ops = [
            f.message for f in result.findings
            if f.rule_name == "required_operations" and not f.passed
        ]
        self.assertTrue(any("park_vehicle" in m for m in missing_ops))
        self.assertTrue(any("calculate_fee" in m for m in missing_ops))

    def test_clean_submission_passes(self) -> None:
        clean_code = """
from abc import ABC, abstractmethod

class Vehicle:
    def __init__(self, plate: str): self.plate = plate

class ParkingSpot:
    def __init__(self, spot_id: str): self.spot_id = spot_id

class ParkingTicket:
    def __init__(self, ticket_id: str, vehicle: Vehicle, spot: ParkingSpot):
        self.ticket_id = ticket_id
        self.vehicle = vehicle
        self.spot = spot

class PricingStrategy(ABC):
    @abstractmethod
    def calculate_fee(self, ticket: ParkingTicket) -> float: pass

class ParkingLot:
    def __init__(self):
        self.spots = []
        self.tickets = []

    def is_available(self) -> bool:
        return True

    def park_vehicle(self, v: Vehicle) -> ParkingTicket:
        return ParkingTicket("t1", v, None)

    def unpark_vehicle(self, ticket_id: str) -> None:
        pass

    def calculate_fee(self, ticket_id: str) -> float:
        return 10.0
"""
        submission = Submission(code=clean_code)
        result = self.evaluator.evaluate(submission, self.parking_problem)

        self.assertTrue(result.passed)
        self.assertEqual(result.score, 100)
        errors = [f for f in result.findings if f.severity == CheckSeverity.ERROR]
        self.assertEqual(len(errors), 0)


if __name__ == "__main__":
    unittest.main()
