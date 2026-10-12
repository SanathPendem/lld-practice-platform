import re
from typing import List
from lld_platform.domain.models import Problem, Submission
from lld_platform.domain.feedback import (
    DeterministicResult,
    QualitativeReview,
    CheckSeverity,
)
from lld_platform.evaluation.base import LLMReviewer


class StubbedLLMReviewer(LLMReviewer):
    """
    A realistic offline LLM reviewer stub.
    Analyzes code structure, docstrings, and deterministic findings to produce
    explainable, human-grade qualitative feedback without requiring API keys.
    """

    def review(
        self,
        submission: Submission,
        problem: Problem,
        deterministic_result: DeterministicResult,
    ) -> QualitativeReview:
        code = submission.code or ""
        strengths: List[str] = []
        improvements: List[str] = []
        recommendations: List[str] = []

        # Analyze design patterns
        has_strategy = bool(re.search(r"class\s+\w*Strategy\b", code, re.IGNORECASE))
        has_factory = bool(re.search(r"class\s+\w*Factory\b|def\s+create_\w+", code, re.IGNORECASE))
        has_enum = bool(re.search(r"class\s+\w*\((?:str,\s*)?Enum\)", code))
        has_abc = bool(re.search(r"\bABC\b|\babstractmethod\b", code))
        has_locks = bool(re.search(r"\bLock\b|\bthreading\b|\bRLock\b", code))

        # Identify strengths
        if has_enum:
            strengths.append(
                "Strong type safety: Leveraged Enums to represent domain states/types rather than primitive strings."
            )
        if has_strategy:
            strengths.append(
                "Good adherence to Open/Closed Principle: Strategy pattern is implemented to decouple volatile business logic."
            )
        if has_abc:
            strengths.append(
                "Polymorphic design: Used abstract base classes or interfaces to enforce contracts."
            )
        if not strengths:
            strengths.append(
                "Foundational structure in place: Core classes have been instantiated for the problem domain."
            )

        # Analyze areas for improvement
        god_class_findings = [
            f for f in deterministic_result.findings
            if f.rule_name == "single_responsibility_god_class" and not f.passed
        ]
        if god_class_findings:
            for g in god_class_findings:
                improvements.append(
                    f"Concentration of concerns in '{g.target_entity}': Class takes on too many disparate roles. "
                    "In an LLD interview, separate coordinators from state holders and calculation engines."
                )

        if not has_strategy and "Strategy Pattern" in " ".join(problem.evaluation_spec.key_design_patterns):
            improvements.append(
                "Missed strategy abstraction: Hardcoded pricing/allocation logic inside concrete methods rather than parameterizing a Strategy object."
            )

        if not has_locks:
            improvements.append(
                "Concurrency consideration: In real-world multi-threaded environments (e.g. simultaneous gate entries or button clicks), "
                "critical sections modifying shared state require synchronization (e.g., threading.Lock or thread-safe queues)."
            )

        if not improvements:
            improvements.append(
                "Edge-case robustness: Consider explicit custom domain exceptions rather than returning None or generic booleans for error cases."
            )

        # Pattern critique
        if has_strategy:
            pattern_critique = (
                "The Strategy pattern is appropriately applied. It isolates the algorithmic variation without introducing unnecessary wrapper layers."
            )
        else:
            pattern_critique = (
                "Consider introducing the Strategy pattern. Decoupling the policy (e.g., fee calculation or elevator dispatch) "
                "from the storage model allows new policies to be introduced without modifying the core domain classes."
            )

        # Trade-offs analysis
        trade_offs = (
            f"Trade-off between simplicity and extensibility in '{problem.title}': "
            "Using concrete class mappings keeps initial code concise, but abstract interfaces provide testability "
            "and resilience against changing business requirements."
        )

        # Recommendations
        if not deterministic_result.passed:
            recommendations.append(
                "Prioritize fixing deterministic errors (missing required entities or operations) before refining pattern abstractions."
            )
        recommendations.append(
            "Add explicit domain exceptions (e.g., SpotUnavailableException, InvalidTicketException) to communicate domain boundary violations."
        )
        recommendations.append(
            "Review method signatures to ensure immutability where appropriate (e.g., returning unmodifiable snapshots or copy of collections)."
        )

        assessment = (
            f"Solid attempt for '{problem.title}'. The submission demonstrates basic domain decomposition "
            f"with a deterministic score of {deterministic_result.score}/100. "
            f"{'Core structural requirements met.' if deterministic_result.passed else 'Key structural requirements are still missing.'}"
        )

        return QualitativeReview(
            assessment=assessment,
            strengths=strengths,
            areas_for_improvement=improvements,
            pattern_critique=pattern_critique,
            trade_offs=trade_offs,
            recommendations=recommendations,
        )


class MockFailingLLMReviewer(LLMReviewer):
    """Used in unit tests to simulate timeouts, network partitions, or outages."""

    def __init__(self, failure_type: str = "timeout") -> None:
        self.failure_type = failure_type

    def review(
        self,
        submission: Submission,
        problem: Problem,
        deterministic_result: DeterministicResult,
    ) -> QualitativeReview:
        if self.failure_type == "timeout":
            raise TimeoutError("LLM service timed out after 5.0 seconds.")
        elif self.failure_type == "connection":
            raise ConnectionError("LLM API endpoint unavailable (503 Service Unavailable).")
        raise RuntimeError("Unexpected failure in LLM reviewer.")
