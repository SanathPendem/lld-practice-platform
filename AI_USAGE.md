# AI Usage & Collaborative Architectural Decisions

This document outlines 4 meaningful AI-assisted decisions made during the design and implementation of the LLD Practice Platform MVP, detailing what was proposed, what was accepted or rejected, and the underlying engineering rationale.

---

### Decision 1: Submission Format (Mermaid Class Diagram DSL vs. AST-Parseable Python Code)
- **What the AI Suggested**:
  Use a Mermaid class diagram text format (e.g. `classDiagram \n class ParkingLot { +parkVehicle() }`) or a structured YAML schema, arguing that diagrams match whiteboard design rounds and are easy to validate with regex.
- **Accepted or Rejected**:
  **Rejected.** Selected Python class outlines parsed via Python's built-in `ast` module.
- **Engineering Rationale**:
  In senior LLD and machine coding interviews, candidates write code: classes, attributes, methods, type annotations, and design patterns. Testing candidate proficiency in a diagramming DSL (like Mermaid or PlantUML) introduces unnecessary friction and tests syntax memorization rather than object-oriented design. Furthermore, regex-based validation is notoriously brittle. Python's built-in Abstract Syntax Tree (`ast`) provides zero-dependency, 100% deterministic static analysis: accurate method counting, attribute tracking, inheritance trees, and exact source line numbers for citations.

---

### Decision 2: Asynchronous Job Architecture (Celery/Redis vs. In-Process ThreadPoolExecutor)
- **What the AI Suggested**:
  Build a full asynchronous job queue using Redis and Celery to manage attempt evaluations, arguing this is how production platforms manage slow AI operations.
- **Accepted or Rejected**:
  **Rejected.** Implemented an in-process `concurrent.futures.ThreadPoolExecutor` with timeout bounds inside `EvaluationPipeline`.
- **Engineering Rationale**:
  The assignment constraints explicitly stated: *"Monolith only. No microservices... Do not build a distributed job system."* Introducing Redis and worker daemons creates heavy installation overhead, external network requirements, and operational complexity for a 2-day take-home MVP. Python's standard `concurrent.futures` isolates slow/hanging LLM calls behind a strict timeout without requiring any external infrastructure.

---

### Decision 3: Evaluation Engine (Single-Prompt LLM vs. Split Deterministic AST + Qualitative Review)
- **What the AI Suggested**:
  Send the candidate's code and problem statement to a single LLM prompt, asking the model to return a combined JSON response containing scores, detected classes, God class warnings, and advice.
- **Accepted or Rejected**:
  **Rejected the single-prompt approach; Accepted the two-tier split architecture.**
- **Engineering Rationale**:
  LLMs are non-deterministic, hallucinate entity presence, and are notoriously unreliable at counting methods or catching subtle omissions. In an interview assessment tool, grading must be explainable and consistent. By anchoring non-negotiables (required entities, required operations, God class thresholds, line citations) in deterministic AST rules, feedback is repeatable and trustworthy. The LLM is used strictly where it excels: qualitative critique of design patterns, trade-offs, and extensibility.

---

### Decision 4: Failure Isolation & Fallback Degradation
- **What the AI Suggested**:
  If the LLM reviewer experiences an error or times out, fail the entire attempt and mark its status as `FAILED`.
- **Accepted or Rejected**:
  **Refined into a tiered fallback strategy.**
- **Engineering Rationale**:
  If an external LLM times out or is unreachable, the learner should not lose their structural feedback. In our implementation, `EvaluationPipeline` traps LLM timeouts and network errors gracefully: the deterministic AST checks are preserved and displayed, while the qualitative section displays a clear notice that AI advice timed out. Only catastrophic engine failures (e.g. out-of-memory or unhandled worker exceptions) mark the attempt as `FAILED`, and the platform explicitly provides `retry_attempt(id)` to allow retrying without re-entering code.
