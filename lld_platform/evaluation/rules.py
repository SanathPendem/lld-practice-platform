import re
from typing import List, Set
from lld_platform.domain.feedback import CheckFinding, CheckSeverity
from lld_platform.evaluation.base import EvaluationRule, EvaluationContext


class SyntaxValidationRule(EvaluationRule):
    @property
    def name(self) -> str:
        return "syntax_validity"

    def evaluate(self, ctx: EvaluationContext) -> List[CheckFinding]:
        if not ctx.syntax_valid:
            return [
                CheckFinding(
                    rule_name=self.name,
                    passed=False,
                    severity=CheckSeverity.ERROR,
                    message=f"Syntax Error: {ctx.syntax_error_message}",
                    line_reference=ctx.syntax_error_line,
                    suggestion="Fix Python syntax errors before architectural rules can be evaluated.",
                )
            ]
        return [
            CheckFinding(
                rule_name=self.name,
                passed=True,
                severity=CheckSeverity.INFO,
                message="Code parsed into valid Python Abstract Syntax Tree (AST).",
            )
        ]


class RequiredEntitiesRule(EvaluationRule):
    @property
    def name(self) -> str:
        return "required_entities"

    def evaluate(self, ctx: EvaluationContext) -> List[CheckFinding]:
        if not ctx.syntax_valid:
            return []

        required = ctx.problem.evaluation_spec.required_entities
        present_classes = {name.lower(): name for name in ctx.classes.keys()}
        findings: List[CheckFinding] = []

        for req in required:
            req_lower = req.lower()
            matched = False

            # Direct or substring match (e.g., HourlyPricingStrategy matches PricingStrategy)
            for cls_lower, original_name in present_classes.items():
                if req_lower in cls_lower or cls_lower in req_lower:
                    matched = True
                    cls_info = ctx.classes[original_name]
                    findings.append(
                        CheckFinding(
                            rule_name=self.name,
                            passed=True,
                            severity=CheckSeverity.INFO,
                            message=f"Required entity '{req}' modeled by class '{original_name}'.",
                            target_entity=original_name,
                            line_reference=cls_info.line_number,
                        )
                    )
                    break

            if not matched:
                findings.append(
                    CheckFinding(
                        rule_name=self.name,
                        passed=False,
                        severity=CheckSeverity.ERROR,
                        message=f"Missing core domain entity: '{req}' is not defined.",
                        target_entity=req,
                        suggestion=f"Define a dedicated class or interface for '{req}' to model its attributes and behaviors explicitly.",
                    )
                )

        return findings


class GodClassRule(EvaluationRule):
    """
    Checks for Single Responsibility Principle (SRP) violations.
    Flags any class having an excessive number of methods or overly concentrated responsibilities.
    """
    @property
    def name(self) -> str:
        return "single_responsibility_god_class"

    def evaluate(self, ctx: EvaluationContext) -> List[CheckFinding]:
        if not ctx.syntax_valid:
            return []

        threshold = ctx.problem.evaluation_spec.god_class_method_threshold
        findings: List[CheckFinding] = []

        for class_name, info in ctx.classes.items():
            # Exclude magic methods like __repr__, __eq__, etc., but keep __init__
            business_methods = [
                m for m in info.methods
                if not (m.startswith("__") and m.endswith("__") and m != "__init__")
            ]
            method_count = len(business_methods)

            if method_count > threshold:
                method_list_preview = ", ".join(business_methods[:6])
                if method_count > 6:
                    method_list_preview += f" ... (+{method_count - 6} more)"

                findings.append(
                    CheckFinding(
                        rule_name=self.name,
                        passed=False,
                        severity=CheckSeverity.WARNING,
                        message=(
                            f"Potential God Class detected in '{class_name}' ({method_count} methods vs threshold {threshold}): "
                            f"[{method_list_preview}]. Responsibilities appear overly concentrated."
                        ),
                        target_entity=class_name,
                        line_reference=info.line_number,
                        suggestion=(
                            f"Decompose '{class_name}' by delegating auxiliary responsibilities "
                            "(e.g., fee calculation, state transitions, strategy selection, or allocation) into dedicated classes."
                        ),
                    )
                )
            else:
                findings.append(
                    CheckFinding(
                        rule_name=self.name,
                        passed=True,
                        severity=CheckSeverity.INFO,
                        message=f"Class '{class_name}' maintains focused responsibility ({method_count} methods).",
                        target_entity=class_name,
                        line_reference=info.line_number,
                    )
                )

        return findings


class RequiredOperationsRule(EvaluationRule):
    @property
    def name(self) -> str:
        return "required_operations"

    def evaluate(self, ctx: EvaluationContext) -> List[CheckFinding]:
        if not ctx.syntax_valid:
            return []

        required_ops = ctx.problem.evaluation_spec.required_operations
        # Collect all methods across all classes + top-level functions
        all_methods: Set[str] = set()
        method_to_class = {}
        for cls_name, info in ctx.classes.items():
            for m in info.methods:
                clean_m = m.lower().replace("_", "")
                all_methods.add(clean_m)
                method_to_class[clean_m] = (cls_name, m, info.method_lines.get(m, info.line_number))

        for fn in ctx.top_level_functions:
            clean_fn = fn.lower().replace("_", "")
            all_methods.add(clean_fn)
            method_to_class[clean_fn] = ("top_level", fn, 1)

        findings: List[CheckFinding] = []

        for req_op in required_ops:
            clean_req = req_op.lower().replace("_", "")
            found = False

            for candidate in all_methods:
                if clean_req in candidate or candidate in clean_req:
                    found = True
                    owner_class, actual_name, line_num = method_to_class[candidate]
                    findings.append(
                        CheckFinding(
                            rule_name=self.name,
                            passed=True,
                            severity=CheckSeverity.INFO,
                            message=f"Required operation '{req_op}' implemented by '{owner_class}.{actual_name}()'.",
                            target_entity=owner_class,
                            line_reference=line_num,
                        )
                    )
                    break

            if not found:
                findings.append(
                    CheckFinding(
                        rule_name=self.name,
                        passed=False,
                        severity=CheckSeverity.ERROR,
                        message=f"Missing core operation: '{req_op}' was not found in any class.",
                        suggestion=f"Expose a public method or API for '{req_op}' on the coordinating domain entity.",
                    )
                )

        return findings


class RelationshipCompositionRule(EvaluationRule):
    """
    Checks if classes model expected structural relationships (composition/association).
    """
    @property
    def name(self) -> str:
        return "relationship_composition"

    def evaluate(self, ctx: EvaluationContext) -> List[CheckFinding]:
        if not ctx.syntax_valid:
            return []

        expected = ctx.problem.evaluation_spec.expected_relationships
        findings: List[CheckFinding] = []

        for parent, expected_children in expected.items():
            parent_info = None
            for cls_name, info in ctx.classes.items():
                if parent.lower() in cls_name.lower():
                    parent_info = info
                    break

            if not parent_info:
                continue

            # Look through field references, base classes, and source code snippet for composition
            source_snippet = "\n".join(ctx.source_lines)
            for child in expected_children:
                pattern = re.compile(rf"\b{child}\b", re.IGNORECASE)
                has_reference = bool(pattern.search(source_snippet))

                if has_reference:
                    findings.append(
                        CheckFinding(
                            rule_name=self.name,
                            passed=True,
                            severity=CheckSeverity.INFO,
                            message=f"Relationship modeled: '{parent_info.name}' references or associates with '{child}'.",
                            target_entity=parent_info.name,
                            line_reference=parent_info.line_number,
                        )
                    )
                else:
                    findings.append(
                        CheckFinding(
                            rule_name=self.name,
                            passed=False,
                            severity=CheckSeverity.WARNING,
                            message=f"Loose coupling / missing association: '{parent_info.name}' does not appear to hold or collaborate with '{child}'.",
                            target_entity=parent_info.name,
                            line_reference=parent_info.line_number,
                            suggestion=f"Consider injecting or composing '{child}' instances inside '{parent_info.name}'.",
                        )
                    )

        return findings
