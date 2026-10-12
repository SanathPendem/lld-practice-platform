import ast
from typing import List, Dict, Optional
from lld_platform.domain.models import Problem, Submission
from lld_platform.domain.feedback import (
    DeterministicResult,
    CheckFinding,
    CheckSeverity,
)
from lld_platform.evaluation.base import (
    EvaluationRule,
    EvaluationContext,
    ClassInfo,
)
from lld_platform.evaluation.rules import (
    SyntaxValidationRule,
    RequiredEntitiesRule,
    GodClassRule,
    RequiredOperationsRule,
    RelationshipCompositionRule,
)


class DeterministicEvaluator:
    """
    Parses Python source code into an AST and evaluates deterministic structural rules.
    Open for extension by registering new EvaluationRule instances.
    """

    def __init__(self, rules: Optional[List[EvaluationRule]] = None) -> None:
        self.rules: List[EvaluationRule] = rules if rules is not None else [
            SyntaxValidationRule(),
            RequiredEntitiesRule(),
            GodClassRule(),
            RequiredOperationsRule(),
            RelationshipCompositionRule(),
        ]

    def add_rule(self, rule: EvaluationRule) -> None:
        """Register a new evaluation rule without altering existing rules."""
        self.rules.append(rule)

    def evaluate(self, submission: Submission, problem: Problem) -> DeterministicResult:
        code = submission.code.strip() if submission.code else ""

        if not code:
            return DeterministicResult(
                passed=False,
                score=0,
                findings=[
                    CheckFinding(
                        rule_name="empty_submission",
                        passed=False,
                        severity=CheckSeverity.ERROR,
                        message="Submission code is completely empty.",
                        suggestion="Provide Python class definitions modeling the domain requirements.",
                    )
                ],
                summary="Empty submission provided.",
            )

        source_lines = code.splitlines()
        context = self._build_context(code, source_lines, submission, problem)

        all_findings: List[CheckFinding] = []
        for rule in self.rules:
            findings = rule.evaluate(context)
            all_findings.extend(findings)

        score, passed = self._calculate_score(all_findings, context.syntax_valid)
        summary = self._build_summary(score, passed, all_findings)

        return DeterministicResult(
            passed=passed,
            score=score,
            findings=all_findings,
            summary=summary,
        )

    def _build_context(
        self,
        code: str,
        source_lines: List[str],
        submission: Submission,
        problem: Problem,
    ) -> EvaluationContext:
        try:
            tree = ast.parse(code)
            classes = self._extract_classes(tree)
            top_level_fns = [
                node.name for node in tree.body if isinstance(node, ast.FunctionDef)
            ]
            return EvaluationContext(
                problem=problem,
                submission=submission,
                source_lines=source_lines,
                syntax_valid=True,
                ast_tree=tree,
                classes=classes,
                top_level_functions=top_level_fns,
            )
        except SyntaxError as e:
            return EvaluationContext(
                problem=problem,
                submission=submission,
                source_lines=source_lines,
                syntax_valid=False,
                ast_tree=None,
                classes={},
                top_level_functions=[],
                syntax_error_message=e.msg,
                syntax_error_line=e.lineno,
            )

    def _extract_classes(self, tree: ast.AST) -> Dict[str, ClassInfo]:
        classes: Dict[str, ClassInfo] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods: List[str] = []
                method_lines: Dict[str, int] = {}
                fields: List[str] = []

                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(item.name)
                        method_lines[item.name] = item.lineno

                        # Extract self.field assignments
                        for subnode in ast.walk(item):
                            if isinstance(subnode, ast.Attribute) and isinstance(subnode.value, ast.Name):
                                if subnode.value.id == "self":
                                    fields.append(subnode.attr)

                bases = [b.id for b in node.bases if isinstance(b, ast.Name)]
                doc = ast.get_docstring(node)

                classes[node.name] = ClassInfo(
                    name=node.name,
                    line_number=node.lineno,
                    methods=methods,
                    method_lines=method_lines,
                    field_references=list(set(fields)),
                    base_classes=bases,
                    docstring=doc,
                )

        return classes

    def _calculate_score(self, findings: List[CheckFinding], syntax_valid: bool) -> tuple[int, bool]:
        if not syntax_valid:
            return 0, False

        score = 100
        has_error = False

        for f in findings:
            if not f.passed:
                if f.severity == CheckSeverity.ERROR:
                    score -= 20
                    has_error = True
                elif f.severity == CheckSeverity.WARNING:
                    score -= 10

        score = max(0, min(100, score))
        passed = (not has_error) and (score >= 60)
        return score, passed

    def _build_summary(self, score: int, passed: bool, findings: List[CheckFinding]) -> str:
        errors = sum(1 for f in findings if not f.passed and f.severity == CheckSeverity.ERROR)
        warnings = sum(1 for f in findings if not f.passed and f.severity == CheckSeverity.WARNING)

        if not passed:
            return f"Deterministic checks failed (Score: {score}/100). Found {errors} error(s) and {warnings} warning(s)."
        if warnings > 0:
            return f"Deterministic checks passed with recommendations (Score: {score}/100). Found {warnings} warning(s)."
        return f"All deterministic checks passed successfully (Score: {score}/100)."
