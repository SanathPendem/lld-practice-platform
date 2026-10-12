from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


class AttemptStatus(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    EVALUATING = "EVALUATING"
    EVALUATED = "EVALUATED"
    FAILED = "FAILED"


class SubmissionFormat(str, Enum):
    PYTHON_CODE = "PYTHON_CODE"


@dataclass
class EvaluationSpec:
    """Target constraints and expectations used by deterministic evaluation."""
    required_entities: List[str]
    required_operations: List[str]
    god_class_method_threshold: int = 7
    expected_relationships: Dict[str, List[str]] = field(default_factory=dict)
    key_design_patterns: List[str] = field(default_factory=list)


@dataclass
class Problem:
    id: str
    title: str
    difficulty: str
    summary: str
    requirements: List[str]
    scope_boundaries: List[str]
    evaluation_spec: EvaluationSpec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "difficulty": self.difficulty,
            "summary": self.summary,
            "requirements": self.requirements,
            "scope_boundaries": self.scope_boundaries,
            "evaluation_spec": {
                "required_entities": self.evaluation_spec.required_entities,
                "required_operations": self.evaluation_spec.required_operations,
                "god_class_method_threshold": self.evaluation_spec.god_class_method_threshold,
                "expected_relationships": self.evaluation_spec.expected_relationships,
                "key_design_patterns": self.evaluation_spec.key_design_patterns,
            }
        }


@dataclass
class Submission:
    code: str
    rationale: str = ""
    format: SubmissionFormat = SubmissionFormat.PYTHON_CODE
    submitted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Attempt:
    id: str
    problem_id: str
    learner_id: str
    submission: Optional[Submission] = None
    status: AttemptStatus = AttemptStatus.DRAFT
    feedback_report: Optional[Any] = None  # Bound to FeedbackReport in runtime
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, problem_id: str, learner_id: str) -> "Attempt":
        return cls(
            id=f"att_{uuid.uuid4().hex[:8]}",
            problem_id=problem_id,
            learner_id=learner_id,
            status=AttemptStatus.DRAFT,
        )

    def submit(self, code: str, rationale: str = "") -> None:
        self.submission = Submission(code=code, rationale=rationale)
        self.status = AttemptStatus.SUBMITTED
        self.error_message = None
        self.updated_at = datetime.now(timezone.utc)

    def mark_evaluating(self) -> None:
        if self.status not in (AttemptStatus.SUBMITTED, AttemptStatus.FAILED):
            raise ValueError(f"Cannot evaluate attempt in status {self.status}")
        self.status = AttemptStatus.EVALUATING
        self.updated_at = datetime.now(timezone.utc)

    def mark_evaluated(self, feedback_report: Any) -> None:
        self.status = AttemptStatus.EVALUATED
        self.feedback_report = feedback_report
        self.error_message = None
        self.updated_at = datetime.now(timezone.utc)

    def mark_failed(self, error_message: str) -> None:
        self.status = AttemptStatus.FAILED
        self.error_message = error_message
        self.updated_at = datetime.now(timezone.utc)
