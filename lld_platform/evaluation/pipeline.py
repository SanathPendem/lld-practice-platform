import concurrent.futures
import logging
from typing import Optional
from lld_platform.domain.models import Problem, Submission
from lld_platform.domain.feedback import (
    FeedbackReport,
    DeterministicResult,
    QualitativeReview,
)
from lld_platform.evaluation.base import Evaluator, LLMReviewer
from lld_platform.evaluation.deterministic import DeterministicEvaluator
from lld_platform.evaluation.llm_reviewer import StubbedLLMReviewer

logger = logging.getLogger(__name__)


class EvaluationPipeline(Evaluator):
    """
    Coordinates the multi-stage evaluation process:
    1. Deterministic AST structural checks (entities, operations, god class, relationships)
    2. Qualitative LLM review (design patterns, trade-offs, code citations)
    3. Failure & timeout isolation: LLM issues do not fail the deterministic feedback.
    """

    def __init__(
        self,
        deterministic_evaluator: Optional[DeterministicEvaluator] = None,
        llm_reviewer: Optional[LLMReviewer] = None,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.deterministic_evaluator = deterministic_evaluator or DeterministicEvaluator()
        self.llm_reviewer = llm_reviewer or StubbedLLMReviewer()
        self.timeout_seconds = timeout_seconds

    def evaluate(
        self,
        submission: Submission,
        problem: Problem,
        attempt_id: str,
    ) -> FeedbackReport:
        # Run deterministic evaluation
        deterministic_result = self.deterministic_evaluator.evaluate(submission, problem)

        # Run qualitative evaluation with defensive fallback & timeout handling
        qualitative_result = self._run_qualitative_review(
            submission, problem, deterministic_result
        )

        overall_passed = deterministic_result.passed
        overall_score = deterministic_result.score

        return FeedbackReport(
            attempt_id=attempt_id,
            problem_id=problem.id,
            passed=overall_passed,
            score=overall_score,
            deterministic=deterministic_result,
            qualitative=qualitative_result,
        )

    def _run_qualitative_review(
        self,
        submission: Submission,
        problem: Problem,
        deterministic_result: DeterministicResult,
    ) -> QualitativeReview:
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    self.llm_reviewer.review,
                    submission,
                    problem,
                    deterministic_result,
                )
                return future.result(timeout=self.timeout_seconds)
        except concurrent.futures.TimeoutError:
            logger.warning("LLM reviewer timed out after %s seconds.", self.timeout_seconds)
            return QualitativeReview(
                assessment="Qualitative LLM review timed out. Deterministic structural checks are complete.",
                strengths=["Structural evaluation completed successfully."],
                areas_for_improvement=["Qualitative advice unavailable due to evaluation timeout."],
                pattern_critique="Pattern critique deferred due to timeout.",
                trade_offs="Analysis deferred.",
                recommendations=["You may retry submission or proceed with deterministic findings."],
            )
        except Exception as e:
            logger.warning("LLM reviewer encountered error: %s", str(e))
            return QualitativeReview(
                assessment=f"Qualitative LLM review unavailable: {str(e)}",
                strengths=[],
                areas_for_improvement=[],
                pattern_critique="Service unavailable.",
                trade_offs="Service unavailable.",
                recommendations=["Please retry to obtain AI qualitative feedback."],
            )
