from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any


class CheckSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class CheckFinding:
    rule_name: str
    passed: bool
    severity: CheckSeverity
    message: str
    target_entity: Optional[str] = None
    line_reference: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "passed": self.passed,
            "severity": self.severity.value,
            "message": self.message,
            "target_entity": self.target_entity,
            "line_reference": self.line_reference,
            "suggestion": self.suggestion,
        }


@dataclass
class DeterministicResult:
    passed: bool
    score: int  # 0 to 100
    findings: List[CheckFinding] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
        }


@dataclass
class QualitativeReview:
    assessment: str
    strengths: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    pattern_critique: str = ""
    trade_offs: str = ""
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "assessment": self.assessment,
            "strengths": self.strengths,
            "areas_for_improvement": self.areas_for_improvement,
            "pattern_critique": self.pattern_critique,
            "trade_offs": self.trade_offs,
            "recommendations": self.recommendations,
        }


@dataclass
class FeedbackReport:
    attempt_id: str
    problem_id: str
    passed: bool
    score: int
    deterministic: DeterministicResult
    qualitative: Optional[QualitativeReview] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "attempt_id": self.attempt_id,
            "problem_id": self.problem_id,
            "passed": self.passed,
            "score": self.score,
            "deterministic": self.deterministic.to_dict(),
            "qualitative": self.qualitative.to_dict() if self.qualitative else None,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ProgressionSummary:
    current_attempt_id: str
    previous_attempt_id: str
    previous_score: int
    current_score: int
    score_delta: int
    resolved_findings: List[str]
    persisting_findings: List[str]
    new_findings: List[str]
    summary_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_attempt_id": self.current_attempt_id,
            "previous_attempt_id": self.previous_attempt_id,
            "previous_score": self.previous_score,
            "current_score": self.current_score,
            "score_delta": self.score_delta,
            "resolved_findings": self.resolved_findings,
            "persisting_findings": self.persisting_findings,
            "new_findings": self.new_findings,
            "summary_text": self.summary_text,
        }
