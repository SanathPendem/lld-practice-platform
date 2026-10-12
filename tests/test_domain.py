import unittest
from lld_platform.domain.models import Attempt, AttemptStatus, Problem, EvaluationSpec, Submission
from lld_platform.domain.feedback import (
    FeedbackReport,
    DeterministicResult,
    CheckFinding,
    CheckSeverity,
    ProgressionSummary,
)
from lld_platform.service.platform_service import PlatformService
from lld_platform.repository.memory import InMemoryAttemptRepository, InMemoryProblemRepository


class TestDomainModels(unittest.TestCase):
    def test_attempt_lifecycle(self) -> None:
        att = Attempt.create(problem_id="parking-lot", learner_id="learner_1")
        self.assertEqual(att.status, AttemptStatus.DRAFT)
        self.assertIsNone(att.submission)

        att.submit(code="class Test: pass", rationale="initial")
        self.assertEqual(att.status, AttemptStatus.SUBMITTED)
        self.assertEqual(att.submission.code, "class Test: pass")

        att.mark_evaluating()
        self.assertEqual(att.status, AttemptStatus.EVALUATING)

        report = FeedbackReport(
            attempt_id=att.id,
            problem_id="parking-lot",
            passed=True,
            score=95,
            deterministic=DeterministicResult(passed=True, score=95),
        )
        att.mark_evaluated(report)
        self.assertEqual(att.status, AttemptStatus.EVALUATED)
        self.assertIsNotNone(att.feedback_report)
        self.assertEqual(att.feedback_report.score, 95)

    def test_attempt_invalid_evaluation_transition(self) -> None:
        att = Attempt.create(problem_id="parking-lot", learner_id="learner_1")
        with self.assertRaises(ValueError):
            att.mark_evaluating()

    def test_attempt_failure_transition(self) -> None:
        att = Attempt.create(problem_id="parking-lot", learner_id="learner_1")
        att.submit(code="some code")
        att.mark_evaluating()
        att.mark_failed("Evaluator out of memory")
        self.assertEqual(att.status, AttemptStatus.FAILED)
        self.assertEqual(att.error_message, "Evaluator out of memory")


class TestProgressionComparison(unittest.TestCase):
    def setUp(self) -> None:
        self.service = PlatformService()

    def test_progression_summary_delta(self) -> None:
        # Create attempt 1
        att1 = self.service.start_attempt("parking-lot")
        att1.submit(code="class A: pass")
        finding_fail = CheckFinding(
            rule_name="required_entities",
            passed=False,
            severity=CheckSeverity.ERROR,
            message="Missing core domain entity: 'ParkingSpot'",
        )
        report1 = FeedbackReport(
            attempt_id=att1.id,
            problem_id="parking-lot",
            passed=False,
            score=40,
            deterministic=DeterministicResult(passed=False, score=40, findings=[finding_fail]),
        )
        att1.mark_evaluated(report1)
        self.service.attempt_repo.save(att1)

        # Create attempt 2
        att2 = self.service.start_attempt("parking-lot")
        att2.submit(code="class ParkingSpot: pass")
        finding_pass = CheckFinding(
            rule_name="required_entities",
            passed=True,
            severity=CheckSeverity.INFO,
            message="Required entity 'ParkingSpot' modeled.",
        )
        report2 = FeedbackReport(
            attempt_id=att2.id,
            problem_id="parking-lot",
            passed=True,
            score=90,
            deterministic=DeterministicResult(passed=True, score=90, findings=[finding_pass]),
        )
        att2.mark_evaluated(report2)
        self.service.attempt_repo.save(att2)

        progression = self.service.compare_progression(att2.id, att1.id)
        self.assertEqual(progression.score_delta, 50)
        self.assertIn("Missing core domain entity: 'ParkingSpot'", progression.resolved_findings)
        self.assertEqual(len(progression.persisting_findings), 0)


if __name__ == "__main__":
    unittest.main()
