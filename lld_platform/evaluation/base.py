from abc import ABC, abstractmethod
import ast
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from lld_platform.domain.models import Problem, Submission
from lld_platform.domain.feedback import (
    CheckFinding,
    DeterministicResult,
    QualitativeReview,
    FeedbackReport,
)


@dataclass
class ClassInfo:
    name: str
    line_number: int
    methods: List[str]
    method_lines: Dict[str, int]
    field_references: List[str]
    base_classes: List[str]
    docstring: Optional[str]


@dataclass
class EvaluationContext:
    problem: Problem
    submission: Submission
    source_lines: List[str]
    syntax_valid: bool
    ast_tree: Optional[ast.AST]
    classes: Dict[str, ClassInfo]
    top_level_functions: List[str]
    syntax_error_message: Optional[str] = None
    syntax_error_line: Optional[int] = None


class EvaluationRule(ABC):
    """
    Open/Closed Principle extension point:
    New deterministic evaluation rules implement this interface
    and plug into the DeterministicEvaluator without altering existing checks.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def evaluate(self, ctx: EvaluationContext) -> List[CheckFinding]:
        pass


class LLMReviewer(ABC):
    """Interface for qualitative LLM design review."""
    @abstractmethod
    def review(
        self,
        submission: Submission,
        problem: Problem,
        deterministic_result: DeterministicResult,
    ) -> QualitativeReview:
        pass


class Evaluator(ABC):
    """Top-level evaluator contract."""
    @abstractmethod
    def evaluate(
        self,
        submission: Submission,
        problem: Problem,
        attempt_id: str,
    ) -> FeedbackReport:
        pass
