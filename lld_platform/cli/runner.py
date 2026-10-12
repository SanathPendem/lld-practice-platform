import argparse
import sys
from pathlib import Path
from typing import Optional
from lld_platform.service.platform_service import PlatformService
from lld_platform.domain.feedback import FeedbackReport, ProgressionSummary, CheckSeverity


def print_banner() -> None:
    print("=" * 72)
    print("      LLD PRACTICE PLATFORM — OBJECT-ORIENTED DESIGN REVIEW      ")
    print("=" * 72)


def display_report(report: FeedbackReport) -> None:
    print("\n" + "-" * 72)
    print(f"FEEDBACK REPORT [Attempt: {report.attempt_id}]")
    print(f"Status: {'PASSED' if report.passed else 'REVISION NEEDED'} | Score: {report.score}/100")
    print("-" * 72)
    print("\n[1] Deterministic Structural Checks:")
    print(f"Summary: {report.deterministic.summary}")
    for idx, finding in enumerate(report.deterministic.findings, 1):
        status_icon = "PASS" if finding.passed else finding.severity
        line_info = f" (line {finding.line_reference})" if finding.line_reference else ""
        print(f"  {idx}. [{status_icon}] {finding.rule_name}{line_info}: {finding.message}")
        if finding.suggestion and not finding.passed:
            print(f"     -> Recommendation: {finding.suggestion}")

    if report.qualitative:
        print("\n[2] Qualitative Design Review (LLM Advisory):")
        print(f"Assessment: {report.qualitative.assessment}")
        if report.qualitative.strengths:
            print("  Strengths:")
            for s in report.qualitative.strengths:
                print(f"   + {s}")
        if report.qualitative.areas_for_improvement:
            print("  Areas for Improvement:")
            for imp in report.qualitative.areas_for_improvement:
                print(f"   - {imp}")
        if report.qualitative.pattern_critique:
            print(f"  Pattern Critique:\n   * {report.qualitative.pattern_critique}")
        if report.qualitative.trade_offs:
            print(f"  Design Trade-Offs:\n   * {report.qualitative.trade_offs}")
        if report.qualitative.recommendations:
            print("  Actionable Next Steps:")
            for r in report.qualitative.recommendations:
                print(f"   > {r}")
    print("-" * 72 + "\n")


def display_progression(progression: ProgressionSummary) -> None:
    print("\n" + "=" * 72)
    print("ATTEMPT PROGRESSION & DELTA ANALYSIS")
    print("=" * 72)
    print(f"Comparing Attempt {progression.previous_attempt_id} -> {progression.current_attempt_id}")
    print(f"Score Delta: {progression.previous_score}/100 -> {progression.current_score}/100 "
          f"({'+' if progression.score_delta >= 0 else ''}{progression.score_delta} pts)")
    print(f"Summary: {progression.summary_text}\n")

    if progression.resolved_findings:
        print("[RESOLVED ISSUES]:")
        for res in progression.resolved_findings:
            print(f"  [FIXED] {res}")

    if progression.persisting_findings:
        print("\n[PERSISTING ISSUES]:")
        for per in progression.persisting_findings:
            print(f"  [STILL FAILING] {per}")

    if progression.new_findings:
        print("\n[NEW ISSUES INTRODUCED]:")
        for new_f in progression.new_findings:
            print(f"  [REGRESSION] {new_f}")
    print("=" * 72 + "\n")


def run_demo(service: Optional[PlatformService] = None) -> None:
    svc = service or PlatformService()
    print_banner()
    print("\n--- Running Automated End-to-End Learner Journey Demo ---")

    # Step 1: Browse Problems
    problems = svc.list_problems()
    print(f"\nAvailable Problems in Platform ({len(problems)}):")
    for p in problems:
        print(f" * [{p.id}] {p.title} ({p.difficulty}) - {p.summary}")

    chosen_problem = "parking-lot"
    prob = svc.get_problem(chosen_problem)
    assert prob is not None
    print(f"\nLearner selected: '{prob.title}'")
    print("Requirements:")
    for r in prob.requirements:
        print(f"  - {r}")
    print("Evaluation Spec Boundaries:")
    for b in prob.scope_boundaries:
        print(f"  - {b}")

    # Step 2: Attempt 1 (Naive solution)
    sample_dir = Path(__file__).parent.parent.parent / "samples"
    bad_code_path = sample_dir / "parking_lot_v1_bad.py"
    bad_code = bad_code_path.read_text(encoding="utf-8") if bad_code_path.exists() else "# Sample naive code"

    print("\n>>> LEARNER SUBMITS ATTEMPT 1 (Naive Implementation with God Class & Missing Entities)...")
    att1 = svc.start_attempt(chosen_problem, learner_id="learner_demo")
    att1 = svc.submit_attempt(
        attempt_id=att1.id,
        code=bad_code,
        rationale="Initial draft with single ParkingLot coordinator handling all operations.",
    )
    assert att1.feedback_report is not None
    display_report(att1.feedback_report)

    # Step 3: Attempt 2 (Refactored clean solution)
    good_code_path = sample_dir / "parking_lot_v2_good.py"
    good_code = good_code_path.read_text(encoding="utf-8") if good_code_path.exists() else "# Sample good code"

    print(">>> LEARNER REVIEWS FEEDBACK, REFACTORS DESIGN, AND SUBMITS ATTEMPT 2...")
    att2 = svc.start_attempt(chosen_problem, learner_id="learner_demo")
    att2 = svc.submit_attempt(
        attempt_id=att2.id,
        code=good_code,
        rationale="Extracted PricingStrategy with Strategy pattern, added ParkingTicket entity, reduced God class.",
    )
    assert att2.feedback_report is not None
    display_report(att2.feedback_report)

    # Step 4: Progression Analysis
    print(">>> LEARNER REVIEWS PROGRESSION ACROSS ATTEMPTS...")
    progression = svc.compare_progression(att2.id, att1.id)
    display_progression(progression)
    print("[SUCCESS] End-to-end learner journey completed successfully!\n")


def interactive_menu(svc: PlatformService) -> None:
    print_banner()
    learner_id = "default_user"

    while True:
        print("\nMain Menu:")
        print("  1. List all LLD problems")
        print("  2. View problem specification & evaluation criteria")
        print("  3. Submit solution from a file")
        print("  4. View attempt history for a problem")
        print("  5. Compare progression between two attempts")
        print("  6. Run automated end-to-end demo")
        print("  7. Exit")

        choice = input("\nEnter choice [1-7]: ").strip()
        if choice == "1":
            problems = svc.list_problems()
            print("\nAvailable Problems:")
            for p in problems:
                print(f"  * {p.id:22} | {p.difficulty:10} | {p.title}")
        elif choice == "2":
            p_id = input("Enter problem ID (e.g., parking-lot, elevator-system): ").strip()
            p = svc.get_problem(p_id)
            if not p:
                print(f"Problem '{p_id}' not found.")
                continue
            print(f"\n=== {p.title} ({p.difficulty}) ===")
            print(f"Summary: {p.summary}\n")
            print("Requirements:")
            for r in p.requirements:
                print(f"  - {r}")
            print("\nEvaluation Scope:")
            for b in p.scope_boundaries:
                print(f"  - {b}")
            print("\nRequired Domain Entities:")
            print("  " + ", ".join(p.evaluation_spec.required_entities))
            print("Required Operations:")
            print("  " + ", ".join(p.evaluation_spec.required_operations))
        elif choice == "3":
            p_id = input("Enter problem ID: ").strip()
            if not svc.get_problem(p_id):
                print(f"Problem '{p_id}' not found.")
                continue
            file_path = input("Enter Python file path containing your design: ").strip()
            path = Path(file_path)
            if not path.is_file():
                print(f"File not found: {file_path}")
                continue
            code = path.read_text(encoding="utf-8")
            rationale = input("Optional design notes/rationale: ").strip()

            att = svc.start_attempt(p_id, learner_id=learner_id)
            print(f"Attempt started ({att.id}). Evaluating...")
            evaluated = svc.submit_attempt(att.id, code, rationale)
            if evaluated.feedback_report:
                display_report(evaluated.feedback_report)
            elif evaluated.status.value == "FAILED":
                print(f"Evaluation failed: {evaluated.error_message}")
        elif choice == "4":
            p_id = input("Enter problem ID: ").strip()
            history = svc.get_attempt_history(learner_id, p_id)
            if not history:
                print("No attempts found.")
                continue
            print(f"\nAttempt History for '{p_id}':")
            for idx, a in enumerate(history, 1):
                score_str = f"{a.feedback_report.score}/100" if a.feedback_report else "N/A"
                print(f"  {idx}. Attempt ID: {a.id} | Status: {a.status.value} | Score: {score_str} | Date: {a.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        elif choice == "5":
            att_prev = input("Enter previous attempt ID: ").strip()
            att_curr = input("Enter current attempt ID: ").strip()
            try:
                prog = svc.compare_progression(att_curr, att_prev)
                display_progression(prog)
            except Exception as e:
                print(f"Error comparing attempts: {e}")
        elif choice == "6":
            run_demo(svc)
        elif choice == "7":
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please enter a number between 1 and 7.")


def main() -> None:
    parser = argparse.ArgumentParser(description="LLD Practice Platform CLI")
    parser.add_argument("--demo", action="store_true", help="Run the automated demonstration flow")
    args = parser.parse_args()

    svc = PlatformService()
    if args.demo:
        run_demo(svc)
    else:
        interactive_menu(svc)


if __name__ == "__main__":
    main()
