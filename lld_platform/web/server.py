import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from pathlib import Path
from typing import Any, Dict
from lld_platform.service.platform_service import PlatformService

logger = logging.getLogger(__name__)

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLD Practice Platform — Object-Oriented Design Feedback</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #090d16;
            --bg-surface: #111827;
            --bg-elevated: #1e293b;
            --border: #334155;
            --primary: #38bdf8;
            --primary-hover: #0ea5e9;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
            --font-mono: 'JetBrains Mono', monospace;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            background-color: var(--bg-base);
            color: var(--text-main);
            font-family: var(--font-sans);
            line-height: 1.5;
            padding: 24px;
        }
        .container { max-width: 1300px; margin: 0 auto; }
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border);
            margin-bottom: 24px;
        }
        h1 { font-size: 1.6rem; font-weight: 700; color: #fff; letter-spacing: -0.02em; }
        .badge {
            background: rgba(56, 189, 248, 0.15);
            color: var(--primary);
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .layout-grid {
            display: grid;
            grid-template-columns: 340px 1fr;
            gap: 24px;
        }
        .panel {
            background: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px;
        }
        .panel h2 {
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 14px;
            color: #f1f5f9;
        }
        select, textarea, input {
            width: 100%;
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            color: var(--text-main);
            border-radius: 8px;
            padding: 10px 12px;
            font-family: inherit;
            font-size: 0.9rem;
            margin-bottom: 14px;
        }
        textarea.code-area {
            font-family: var(--font-mono);
            font-size: 0.85rem;
            height: 380px;
            resize: vertical;
            white-space: pre;
            tab-size: 4;
        }
        .btn-group { display: flex; gap: 10px; margin-bottom: 14px; }
        button {
            cursor: pointer;
            border: none;
            border-radius: 8px;
            padding: 10px 18px;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.2s;
        }
        .btn-primary { background: var(--primary); color: #0f172a; }
        .btn-primary:hover { background: var(--primary-hover); }
        .btn-secondary { background: var(--bg-elevated); color: var(--text-muted); border: 1px solid var(--border); }
        .btn-secondary:hover { color: var(--text-main); border-color: var(--primary); }
        .req-list, .boundary-list { list-style: none; font-size: 0.88rem; color: var(--text-muted); margin-bottom: 16px; }
        .req-list li { margin-bottom: 8px; position: relative; padding-left: 18px; }
        .req-list li::before { content: "•"; position: absolute; left: 0; color: var(--primary); }
        .finding-card {
            background: var(--bg-elevated);
            border-left: 4px solid var(--border);
            border-radius: 6px;
            padding: 12px 14px;
            margin-bottom: 10px;
            font-size: 0.88rem;
        }
        .finding-card.pass { border-color: var(--success); }
        .finding-card.warn { border-color: var(--warning); }
        .finding-card.error { border-color: var(--danger); }
        .finding-title { font-weight: 600; display: flex; justify-content: space-between; margin-bottom: 4px; }
        .finding-desc { color: var(--text-muted); }
        .finding-suggestion { color: #fde047; font-size: 0.82rem; margin-top: 6px; }
        .score-pill {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--primary);
            margin-bottom: 12px;
        }
        .history-item {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            cursor: pointer;
            font-size: 0.85rem;
        }
        .history-item:hover { border-color: var(--primary); }
        .delta-card {
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 16px;
            font-size: 0.88rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div>
                <h1>LLD Practice Platform</h1>
                <p style="color: var(--text-muted); font-size: 0.88rem;">Object-Oriented Design Practice with Hybrid Deterministic & AI Feedback</p>
            </div>
            <div class="badge">Local Monolith Prototype</div>
        </header>

        <div class="layout-grid">
            <aside>
                <div class="panel">
                    <h2>Select Problem</h2>
                    <select id="problemSelect"></select>
                    <div id="problemDetails"></div>
                </div>

                <div class="panel" style="margin-top: 20px;">
                    <h2>Attempt History</h2>
                    <div id="historyList"><p style="color: var(--text-muted); font-size: 0.85rem;">No attempts yet.</p></div>
                </div>
            </aside>

            <main>
                <div class="panel">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <h2>Design Submission (Python Class Outline & API)</h2>
                        <div class="btn-group" style="margin: 0;">
                            <button class="btn-secondary" id="btnLoadBad">Load Naive Attempt</button>
                            <button class="btn-secondary" id="btnLoadGood">Load Refactored Attempt</button>
                        </div>
                    </div>
                    <textarea id="codeEditor" class="code-area" placeholder="# Write or paste your object-oriented class design here..."></textarea>
                    <input type="text" id="rationaleInput" placeholder="Design rationale (e.g. 'Used Strategy pattern for pricing calculations')">
                    <button class="btn-primary" id="btnSubmit">Submit Design for Evaluation</button>
                </div>

                <div class="panel" style="margin-top: 20px;" id="feedbackPanel">
                    <h2>Evaluation Feedback</h2>
                    <div id="feedbackContent">
                        <p style="color: var(--text-muted);">Submit your design above to receive deterministic structural analysis and qualitative architectural feedback.</p>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <script>
        let currentProblemId = "parking-lot";
        let attemptsHistory = [];

        async function fetchProblems() {
            const res = await fetch("/api/problems");
            const data = await res.json();
            const select = document.getElementById("problemSelect");
            select.innerHTML = data.map(p => `<option value="${p.id}">${p.title} (${p.difficulty})</option>`).join("");
            select.addEventListener("change", (e) => {
                currentProblemId = e.target.value;
                loadProblem(currentProblemId);
                loadHistory();
            });
            loadProblem(data[0].id);
            loadHistory();
        }

        async function loadProblem(id) {
            const res = await fetch(`/api/problems/${id}`);
            const p = await res.json();
            currentProblemId = p.id;
            const container = document.getElementById("problemDetails");
            container.innerHTML = `
                <p style="font-size: 0.88rem; color: #cbd5e1; margin-bottom: 12px;">${p.summary}</p>
                <h3 style="font-size: 0.9rem; margin-bottom: 6px; color: var(--primary);">Requirements:</h3>
                <ul class="req-list">${p.requirements.map(r => `<li>${r}</li>`).join("")}</ul>
                <h3 style="font-size: 0.9rem; margin-bottom: 6px; color: var(--primary);">Scope Boundaries:</h3>
                <ul class="req-list">${p.scope_boundaries.map(b => `<li>${b}</li>`).join("")}</ul>
            `;
        }

        async function loadHistory() {
            const res = await fetch(`/api/attempts?problem_id=${currentProblemId}`);
            attemptsHistory = await res.json();
            const list = document.getElementById("historyList");
            if (!attemptsHistory.length) {
                list.innerHTML = `<p style="color: var(--text-muted); font-size: 0.85rem;">No attempts yet for this problem.</p>`;
                return;
            }
            list.innerHTML = attemptsHistory.map((att, idx) => `
                <div class="history-item" onclick="viewAttempt('${att.id}')">
                    <div style="display:flex; justify-content:space-between; font-weight:600;">
                        <span>Attempt #${idx + 1} (${att.id})</span>
                        <span style="color: ${att.feedback_report?.passed ? 'var(--success)' : 'var(--warning)'}">
                            ${att.feedback_report?.score ?? 0}/100
                        </span>
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${new Date(att.created_at).toLocaleTimeString()}</div>
                </div>
            `).join("");
        }

        window.viewAttempt = function(attId) {
            const att = attemptsHistory.find(a => a.id === attId);
            if (att && att.feedback_report) {
                renderFeedback(att.feedback_report);
            }
        };

        async function submitAttempt() {
            const code = document.getElementById("codeEditor").value;
            const rationale = document.getElementById("rationaleInput").value;
            if (!code.trim()) { alert("Please provide code before submitting."); return; }

            const btn = document.getElementById("btnSubmit");
            btn.disabled = true;
            btn.innerText = "Evaluating Design...";

            const res = await fetch("/api/attempts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ problem_id: currentProblemId, code, rationale })
            });
            const data = await res.json();
            btn.disabled = false;
            btn.innerText = "Submit Design for Evaluation";

            if (data.feedback_report) {
                renderFeedback(data.feedback_report);
                await loadHistory();
                if (attemptsHistory.length >= 2) {
                    checkProgression(attemptsHistory[attemptsHistory.length - 1].id, attemptsHistory[attemptsHistory.length - 2].id);
                }
            } else if (data.status === "FAILED") {
                document.getElementById("feedbackContent").innerHTML = `
                    <div class="finding-card error">
                        <div class="finding-title">Evaluation Failure</div>
                        <div class="finding-desc">${data.error_message}</div>
                    </div>
                `;
            }
        }

        async function checkProgression(currId, prevId) {
            const res = await fetch(`/api/progression?curr=${currId}&prev=${prevId}`);
            if (res.ok) {
                const prog = await res.json();
                const container = document.getElementById("feedbackContent");
                const deltaHtml = `
                    <div class="delta-card">
                        <div style="font-weight: 700; color: var(--success); margin-bottom: 4px;">Progression Delta: ${prog.summary_text}</div>
                        ${prog.resolved_findings.length ? `<div style="margin-top:6px;"><strong>Resolved:</strong> ${prog.resolved_findings.join(", ")}</div>` : ''}
                    </div>
                `;
                container.insertAdjacentHTML('afterbegin', deltaHtml);
            }
        }

        function renderFeedback(report) {
            const findingsHtml = report.deterministic.findings.map(f => {
                const cls = f.passed ? 'pass' : (f.severity === 'ERROR' ? 'error' : 'warn');
                return `
                    <div class="finding-card ${cls}">
                        <div class="finding-title">
                            <span>[${f.passed ? 'PASS' : f.severity}] ${f.rule_name}</span>
                            ${f.line_reference ? `<span style="font-size: 0.8rem; color: var(--text-muted);">line ${f.line_reference}</span>` : ''}
                        </div>
                        <div class="finding-desc">${f.message}</div>
                        ${f.suggestion ? `<div class="finding-suggestion">💡 ${f.suggestion}</div>` : ''}
                    </div>
                `;
            }).join("");

            const qual = report.qualitative;
            const qualHtml = qual ? `
                <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid var(--border);">
                    <h3 style="font-size: 1rem; color: var(--primary); margin-bottom: 8px;">Qualitative Architectural Review</h3>
                    <p style="font-size: 0.9rem; margin-bottom: 12px;">${qual.assessment}</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 14px;">
                        <div style="background: var(--bg-elevated); padding: 12px; border-radius: 8px;">
                            <strong style="color: var(--success); font-size: 0.85rem;">Strengths:</strong>
                            <ul style="padding-left: 18px; font-size: 0.82rem; color: var(--text-muted); margin-top: 6px;">
                                ${qual.strengths.map(s => `<li>${s}</li>`).join("")}
                            </ul>
                        </div>
                        <div style="background: var(--bg-elevated); padding: 12px; border-radius: 8px;">
                            <strong style="color: var(--warning); font-size: 0.85rem;">Improvement Areas:</strong>
                            <ul style="padding-left: 18px; font-size: 0.82rem; color: var(--text-muted); margin-top: 6px;">
                                ${qual.areas_for_improvement.map(i => `<li>${i}</li>`).join("")}
                            </ul>
                        </div>
                    </div>
                    <div style="background: var(--bg-elevated); padding: 12px; border-radius: 8px; font-size: 0.85rem; margin-bottom: 12px;">
                        <strong style="color: var(--primary);">Design Pattern Critique:</strong>
                        <p style="color: var(--text-muted); margin-top: 4px;">${qual.pattern_critique}</p>
                    </div>
                </div>
            ` : '';

            document.getElementById("feedbackContent").innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <div class="score-pill">${report.score}/100</div>
                    <span style="font-weight: 600; color: ${report.passed ? 'var(--success)' : 'var(--warning)'};">
                        ${report.passed ? 'PASSED STRUCTURAL SPEC' : 'NEEDS REVISION'}
                    </span>
                </div>
                <p style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 16px;">${report.deterministic.summary}</p>
                <h3 style="font-size: 0.95rem; margin-bottom: 8px;">Deterministic Checks</h3>
                ${findingsHtml}
                ${qualHtml}
            `;
        }

        // Attach sample loaders
        document.getElementById("btnLoadBad").addEventListener("click", async () => {
            const res = await fetch("/api/samples/bad");
            const text = await res.text();
            document.getElementById("codeEditor").value = text;
            document.getElementById("rationaleInput").value = "Attempt 1: Monolithic ParkingLot handling all parking and calculation.";
        });

        document.getElementById("btnLoadGood").addEventListener("click", async () => {
            const res = await fetch("/api/samples/good");
            const text = await res.text();
            document.getElementById("codeEditor").value = text;
            document.getElementById("rationaleInput").value = "Attempt 2: Decomposed with Strategy pattern and ParkingTicket entity.";
        });

        document.getElementById("btnSubmit").addEventListener("click", submitAttempt);
        fetchProblems();
    </script>
</body>
</html>
"""


class PlatformHTTPHandler(BaseHTTPRequestHandler):
    service = PlatformService()

    def do_GET(self) -> None:
        url = urlparse(self.path)
        path = url.path

        if path == "/" or path == "/index.html":
            self._send_html(HTML_PAGE)
            return

        if path == "/api/problems":
            problems = [p.to_dict() for p in self.service.list_problems()]
            self._send_json(problems)
            return

        if path.startswith("/api/problems/"):
            p_id = path.split("/api/problems/")[1]
            problem = self.service.get_problem(p_id)
            if problem:
                self._send_json(problem.to_dict())
            else:
                self._send_error(404, "Problem not found")
            return

        if path == "/api/attempts":
            params = parse_qs(url.query)
            p_id = params.get("problem_id", [None])[0]
            learner_id = params.get("learner_id", ["web_learner"])[0]
            if p_id:
                history = self.service.get_attempt_history(learner_id, p_id)
            else:
                history = self.service.attempt_repo.list_by_learner(learner_id)
            out = []
            for a in history:
                out.append({
                    "id": a.id,
                    "problem_id": a.problem_id,
                    "status": a.status.value,
                    "created_at": a.created_at.isoformat(),
                    "feedback_report": a.feedback_report.to_dict() if a.feedback_report else None,
                })
            self._send_json(out)
            return

        if path == "/api/progression":
            params = parse_qs(url.query)
            curr = params.get("curr", [None])[0]
            prev = params.get("prev", [None])[0]
            if not curr or not prev:
                self._send_error(400, "Missing curr or prev attempt ID")
                return
            try:
                prog = self.service.compare_progression(curr, prev)
                self._send_json(prog.to_dict())
            except Exception as e:
                self._send_error(400, str(e))
            return

        if path == "/api/samples/bad":
            p = Path(__file__).parent.parent.parent / "samples" / "parking_lot_v1_bad.py"
            content = p.read_text(encoding="utf-8") if p.exists() else "# Bad sample missing"
            self._send_text(content)
            return

        if path == "/api/samples/good":
            p = Path(__file__).parent.parent.parent / "samples" / "parking_lot_v2_good.py"
            content = p.read_text(encoding="utf-8") if p.exists() else "# Good sample missing"
            self._send_text(content)
            return

        self._send_error(404, "Endpoint not found")

    def do_POST(self) -> None:
        url = urlparse(self.path)
        if url.path == "/api/attempts":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                data = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                self._send_error(400, "Invalid JSON body")
                return

            problem_id = data.get("problem_id", "parking-lot")
            code = data.get("code", "")
            rationale = data.get("rationale", "")
            learner_id = data.get("learner_id", "web_learner")

            att = self.service.start_attempt(problem_id, learner_id=learner_id)
            evaluated = self.service.submit_attempt(att.id, code, rationale)

            response_data = {
                "id": evaluated.id,
                "problem_id": evaluated.problem_id,
                "status": evaluated.status.value,
                "error_message": evaluated.error_message,
                "feedback_report": evaluated.feedback_report.to_dict() if evaluated.feedback_report else None,
            }
            self._send_json(response_data)
            return

        self._send_error(404, "Endpoint not found")

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_html(self, html: str, status: int = 200) -> None:
        payload = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, text: str, status: int = 200) -> None:
        payload = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _send_error(self, code: int, message: str) -> None:
        self._send_json({"error": message}, status=code)

    def log_message(self, format: str, *args: Any) -> None:
        # Silence default request logging to keep console clean
        return


def run_server(port: int = 8080) -> None:
    server_address = ("", port)
    httpd = HTTPServer(server_address, PlatformHTTPHandler)
    print(f"LLD Platform Web Server running at http://localhost:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down web server...")
        httpd.server_close()


if __name__ == "__main__":
    run_server()
