import unittest
from typing import List
from lld_platform.domain.models import Submission
from lld_platform.domain.feedback import CheckFinding, CheckSeverity
from lld_platform.problems.catalog import Catalog
from lld_platform.evaluation.base import EvaluationRule, EvaluationContext
from lld_platform.evaluation.deterministic import DeterministicEvaluator


class DocstringCoverageRule(EvaluationRule):
    """
    Custom extension rule added without modifying existing evaluation logic.
    Flags classes that lack docstring documentation.
    """
    @property
    def name(self) -> str:
        return "docstring_documentation"

    def evaluate(self, ctx: EvaluationContext) -> List[CheckFinding]:
        if not ctx.syntax_valid:
            return []

        findings: List[CheckFinding] = []
        for name, info in ctx.classes.items():
            if not info.docstring:
                findings.append(
                    CheckFinding(
                        rule_name=self.name,
                        passed=False,
                        severity=CheckSeverity.WARNING,
                        message=f"Class '{name}' lacks an explanatory docstring.",
                        target_entity=name,
                        line_reference=info.line_number,
                        suggestion="Add a class docstring clarifying its responsibility and invariants.",
                    )
                )
            else:
                findings.append(
                    CheckFinding(
                        rule_name=self.name,
                        passed=True,
                        severity=CheckSeverity.INFO,
                        message=f"Class '{name}' has valid documentation.",
                        target_entity=name,
                        line_reference=info.line_number,
                    )
                )
        return findings


class TestExtensibility(unittest.TestCase):
    def test_add_custom_evaluation_rule_without_modifying_core(self) -> None:
        evaluator = DeterministicEvaluator()
        initial_rule_count = len(evaluator.rules)

        # Register custom rule dynamically
        custom_rule = DocstringCoverageRule()
        evaluator.add_rule(custom_rule)
        self.assertEqual(len(evaluator.rules), initial_rule_count + 1)

        catalog = Catalog()
        problem = catalog.get("parking-lot")
        self.assertIsNotNone(problem)

        code_without_docstrings = """
class Vehicle: pass
class ParkingSpot: pass
class ParkingLot: pass
class ParkingTicket: pass
class PricingStrategy: pass
"""
        submission = Submission(code=code_without_docstrings)
        result = evaluator.evaluate(submission, problem)

        # Confirm the new rule executed and reported findings
        doc_findings = [f for f in result.findings if f.rule_name == "docstring_documentation"]
        self.assertEqual(len(doc_findings), 5)
        self.assertTrue(all(not f.passed for f in doc_findings))
        self.assertIn("Vehicle", [f.target_entity for f in doc_findings])


if __name__ == "__main__":
    unittest.main()
