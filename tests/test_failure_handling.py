import unittest
from lld_platform.domain.models import Submission, AttemptStatus
from lld_platform.problems.catalog import Catalog
from lld_platform.evaluation.deterministic import DeterministicEvaluator
from lld_platform.evaluation.pipeline import EvaluationPipeline
from lld_platform.evaluation.llm_reviewer import MockFailingLLMReviewer
from lld_platform.service.platform_service import PlatformService
from lld_platform.evaluation.base import Evaluator


class CrashingEvaluator(Evaluator):
    def evaluate(self, submission, problem, attempt_id):
        raise MemoryError("Simulated unrecoverable worker memory crash during AST synthesis.")


class TestFailureHandling(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = Catalog()
        self.problem = self.catalog.get("parking-lot")
        self.assertIsNotNone(self.problem)

    def test_empty_submission_handling(self) -> None:
        evaluator = DeterministicEvaluator()
        empty_sub = Submission(code="    \n   \t  ")
        result = evaluator.evaluate(empty_sub, self.problem)

        self.assertFalse(result.passed)
        self.assertEqual(result.score, 0)
        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].rule_name, "empty_submission")
        self.assertIn("empty", result.findings[0].message.lower())

    def test_llm_reviewer_timeout_fallback(self) -> None:
        # LLM reviewer times out, but deterministic checks should still be preserved
        timing_out_reviewer = MockFailingLLMReviewer(failure_type="timeout")
        pipeline = EvaluationPipeline(llm_reviewer=timing_out_reviewer, timeout_seconds=0.1)

        valid_code = "class Vehicle: pass\nclass ParkingSpot: pass\nclass ParkingLot: pass"
        sub = Submission(code=valid_code)
        report = pipeline.evaluate(sub, self.problem, attempt_id="att_timeout")

        # Deterministic result is intact
        self.assertIsNotNone(report.deterministic)
        # Qualitative review provided graceful fallback message rather than crashing
        self.assertIsNotNone(report.qualitative)
        self.assertIn("timed out", report.qualitative.assessment.lower())
        self.assertTrue(len(report.qualitative.recommendations) > 0)

    def test_llm_reviewer_network_failure_fallback(self) -> None:
        failing_reviewer = MockFailingLLMReviewer(failure_type="connection")
        pipeline = EvaluationPipeline(llm_reviewer=failing_reviewer)

        sub = Submission(code="class Vehicle: pass")
        report = pipeline.evaluate(sub, self.problem, attempt_id="att_conn_err")

        self.assertIsNotNone(report.deterministic)
        self.assertIsNotNone(report.qualitative)
        self.assertIn("unavailable", report.qualitative.assessment.lower())

    def test_catastrophic_evaluator_exception_marks_attempt_failed_and_retries(self) -> None:
        crashing_evaluator = CrashingEvaluator()
        service = PlatformService(evaluator=crashing_evaluator)

        att = service.start_attempt("parking-lot")
        evaluated = service.submit_attempt(att.id, "class Test: pass")

        # Attempt should transition to FAILED with descriptive error message
        self.assertEqual(evaluated.status, AttemptStatus.FAILED)
        self.assertIsNotNone(evaluated.error_message)
        self.assertIn("Simulated unrecoverable worker memory crash", evaluated.error_message)

        # Now test that learner can retry the failed attempt with a working evaluator
        service.evaluator = EvaluationPipeline()
        retried = service.retry_attempt(
            failed_attempt_id=att.id,
            code="class Vehicle: pass\nclass ParkingSpot: pass\nclass ParkingLot: pass\nclass ParkingTicket: pass\nclass PricingStrategy: pass",
        )
        self.assertEqual(retried.status, AttemptStatus.EVALUATED)
        self.assertIsNone(retried.error_message)
        self.assertIsNotNone(retried.feedback_report)


if __name__ == "__main__":
    unittest.main()
