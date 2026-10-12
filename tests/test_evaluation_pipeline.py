import unittest
from lld_platform.domain.models import Submission
from lld_platform.problems.catalog import Catalog
from lld_platform.evaluation.pipeline import EvaluationPipeline
from lld_platform.evaluation.llm_reviewer import StubbedLLMReviewer


class TestEvaluationPipeline(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = Catalog()
        self.problem = self.catalog.get("elevator-system")
        self.assertIsNotNone(self.problem)
        self.pipeline = EvaluationPipeline(llm_reviewer=StubbedLLMReviewer())

    def test_pipeline_runs_deterministic_and_qualitative(self) -> None:
        elevator_code = """
from enum import Enum

class ElevatorState(Enum):
    IDLE = 1
    MOVING_UP = 2
    MOVING_DOWN = 3

class Floor:
    def __init__(self, level: int): self.level = level

class Request:
    def __init__(self, floor: int): self.floor = floor

class ElevatorCar:
    def __init__(self, id: str):
        self.id = id
        self.state = ElevatorState.IDLE
    def add_request(self, req: Request): pass
    def step(self): pass
    def open_doors(self): pass

class ElevatorController:
    def __init__(self):
        self.cars = []
    def request_elevator(self, floor: int): pass
    def step(self): pass
"""
        submission = Submission(code=elevator_code)
        report = self.pipeline.evaluate(submission, self.problem, attempt_id="att_test_1")

        self.assertTrue(report.passed)
        self.assertGreaterEqual(report.score, 90)
        self.assertIsNotNone(report.deterministic)
        self.assertIsNotNone(report.qualitative)
        self.assertTrue(len(report.qualitative.strengths) > 0)
        self.assertTrue(len(report.qualitative.areas_for_improvement) > 0)
        self.assertTrue(bool(report.qualitative.pattern_critique))


if __name__ == "__main__":
    unittest.main()
