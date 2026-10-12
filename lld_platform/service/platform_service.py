import logging
from typing import List, Optional
from lld_platform.domain.models import Attempt, AttemptStatus, Problem
from lld_platform.domain.feedback import FeedbackReport, ProgressionSummary
from lld_platform.repository.base import AttemptRepository, ProblemRepository
from lld_platform.repository.memory import InMemoryAttemptRepository, InMemoryProblemRepository
from lld_platform.evaluation.base import Evaluator
from lld_platform.evaluation.pipeline import EvaluationPipeline

logger = logging.getLogger(__name__)


class PlatformService:
    """
    Coordinates learner practice sessions, submissions, evaluation lifecycle,
    and history progression analysis.
    """

    def __init__(
        self,
        problem_repo: Optional[ProblemRepository] = None,
        attempt_repo: Optional[AttemptRepository] = None,
        evaluator: Optional[Evaluator] = None,
    ) -> None:
        self.problem_repo = problem_repo or InMemoryProblemRepository()
        self.attempt_repo = attempt_repo or InMemoryAttemptRepository()
        self.evaluator = evaluator or EvaluationPipeline()

    def list_problems(self) -> List[Problem]:
        return self.problem_repo.list_all()

    def get_problem(self, problem_id: str) -> Optional[Problem]:
        return self.problem_repo.get(problem_id)

    def start_attempt(self, problem_id: str, learner_id: str = "learner_1") -> Attempt:
        problem = self.problem_repo.get(problem_id)
        if not problem:
            raise ValueError(f"Problem '{problem_id}' does not exist.")

        attempt = Attempt.create(problem_id=problem_id, learner_id=learner_id)
        self.attempt_repo.save(attempt)
        return attempt

    def submit_attempt(
        self,
        attempt_id: str,
        code: str,
        rationale: str = "",
    ) -> Attempt:
        attempt = self.attempt_repo.get_by_id(attempt_id)
        if not attempt:
            raise ValueError(f"Attempt '{attempt_id}' not found.")

        problem = self.problem_repo.get(attempt.problem_id)
        if not problem:
            raise ValueError(f"Problem '{attempt.problem_id}' not found.")

        attempt.submit(code=code, rationale=rationale)
        attempt.mark_evaluating()
        self.attempt_repo.save(attempt)

        try:
            report = self.evaluator.evaluate(
                submission=attempt.submission,
                problem=problem,
                attempt_id=attempt.id,
            )
            attempt.mark_evaluated(report)
        except Exception as e:
            logger.exception("Evaluation failed catastrophically for attempt %s", attempt_id)
            attempt.mark_failed(f"Evaluation failed: {str(e)}")

        self.attempt_repo.save(attempt)
        return attempt

    def retry_attempt(
        self,
        failed_attempt_id: str,
        code: Optional[str] = None,
        rationale: Optional[str] = None,
    ) -> Attempt:
        """
        Allows retrying a failed attempt, either re-evaluating with updated code
        or retrying the existing submission.
        """
        attempt = self.attempt_repo.get_by_id(failed_attempt_id)
        if not attempt:
            raise ValueError(f"Attempt '{failed_attempt_id}' not found.")

        sub_code = code if code is not None else (attempt.submission.code if attempt.submission else "")
        sub_rat = rationale if rationale is not None else (attempt.submission.rationale if attempt.submission else "")

        attempt.status = AttemptStatus.SUBMITTED
        return self.submit_attempt(failed_attempt_id, sub_code, sub_rat)

    def get_attempt_history(self, learner_id: str, problem_id: str) -> List[Attempt]:
        return self.attempt_repo.list_by_learner_and_problem(learner_id, problem_id)

    def compare_progression(
        self,
        current_attempt_id: str,
        previous_attempt_id: str,
    ) -> ProgressionSummary:
        curr = self.attempt_repo.get_by_id(current_attempt_id)
        prev = self.attempt_repo.get_by_id(previous_attempt_id)

        if not curr or not prev:
            raise ValueError("Both current and previous attempts must exist.")
        if not curr.feedback_report or not prev.feedback_report:
            raise ValueError("Both attempts must have completed feedback reports.")

        curr_report: FeedbackReport = curr.feedback_report
        prev_report: FeedbackReport = prev.feedback_report

        prev_failures = {
            f.message for f in prev_report.deterministic.findings if not f.passed
        }
        curr_failures = {
            f.message for f in curr_report.deterministic.findings if not f.passed
        }

        resolved = list(prev_failures - curr_failures)
        persisting = list(prev_failures & curr_failures)
        new_issues = list(curr_failures - prev_failures)
        score_delta = curr_report.score - prev_report.score

        if score_delta > 0:
            summary_text = (
                f"Great improvement! Score increased by {score_delta} points "
                f"({prev_report.score} -> {curr_report.score}). Resolved {len(resolved)} issue(s)."
            )
        elif score_delta < 0:
            summary_text = (
                f"Score decreased by {abs(score_delta)} points "
                f"({prev_report.score} -> {curr_report.score}). {len(new_issues)} new issue(s) introduced."
            )
        else:
            summary_text = (
                f"Score unchanged at {curr_report.score}. "
                f"{len(persisting)} issue(s) remaining."
            )

        return ProgressionSummary(
            current_attempt_id=current_attempt_id,
            previous_attempt_id=previous_attempt_id,
            previous_score=prev_report.score,
            current_score=curr_report.score,
            score_delta=score_delta,
            resolved_findings=resolved,
            persisting_findings=persisting,
            new_findings=new_issues,
            summary_text=summary_text,
        )
