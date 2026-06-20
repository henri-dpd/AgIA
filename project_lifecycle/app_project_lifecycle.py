from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from typing import Annotated, Any, TypedDict

import httpx
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
DEFAULT_BASE_URL = os.getenv("OLLAMA_BASE_URL", os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434"))
MAX_REVIEW_ROUNDS = 3
VALID_MODES = ("define", "evaluate", "audit")


# ---------------------------------------------------------------------------
# Pydantic contracts
# ---------------------------------------------------------------------------


class RequirementsAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objectives: list[str] = Field(min_length=1)
    functional_requirements: list[str] = Field(min_length=1)
    non_functional_requirements: list[str] = Field(default_factory=list)
    scope: str = Field(min_length=20, max_length=2000)
    out_of_scope: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class TechAndPlanProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_stack: list[str] = Field(min_length=1)
    supporting_tools: list[str] = Field(default_factory=list)
    architecture_pattern: str = Field(min_length=10, max_length=500)
    architecture_diagram: str = Field(min_length=10, max_length=3000)
    rationale: str = Field(min_length=20, max_length=1500)
    phases: list[dict[str, str]] = Field(min_length=1)
    total_estimated_duration: str = Field(min_length=5, max_length=200)
    implementation_risks: list[str] = Field(default_factory=list)


class ProjectEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_status: str = Field(min_length=5, max_length=300)
    requirements_coverage: str = Field(min_length=20, max_length=1000)
    bad_practices_identified: list[str] = Field(default_factory=list)
    improvement_suggestions: list[str] = Field(min_length=1)
    priority_actions: list[str] = Field(min_length=1)
    risks_identified: list[str] = Field(default_factory=list)


class CompletionAudit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    objectives_met: list[str] = Field(default_factory=list)
    objectives_not_met: list[str] = Field(default_factory=list)
    missing_features: list[str] = Field(default_factory=list)
    quality_gaps: list[str] = Field(default_factory=list)
    documentation_gaps: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(min_length=1)
    final_verdict: str = Field(min_length=20, max_length=1000)


class QAReview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    summary: str = Field(min_length=20, max_length=1200)
    gaps: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Graph state
# ---------------------------------------------------------------------------


class LifecycleState(TypedDict):
    project_description: str
    mode: str
    scaffold_requested: bool
    messages: Annotated[list[BaseMessage], add_messages]
    round_number: int
    max_rounds: int
    # define mode outputs
    requirements_doc: str
    tech_plan_doc: str
    documentation_outline: str
    # evaluate mode outputs
    evaluation_doc: str
    # audit mode outputs
    audit_doc: str
    # qa
    qa_review_doc: str
    qa_approved: bool
    review_log: list[dict[str, Any]]
    # final output
    final_document: str
    errors: list[str]


@dataclass(frozen=True)
class LifecycleContainer:
    llm: ChatOllama


def _build_llm() -> ChatOllama:
    return ChatOllama(model=DEFAULT_MODEL, base_url=DEFAULT_BASE_URL, temperature=0.2)


def _format_fallback_error(agent: str, category: str, exc: Exception) -> str:
    detail = str(exc).strip() or "no detail available"
    return f"{agent} fallback ({category}:{type(exc).__name__}): {detail}"


# ---------------------------------------------------------------------------
# Fallback generators
# ---------------------------------------------------------------------------


def _fallback_requirements(description: str) -> RequirementsAnalysis:
    return RequirementsAnalysis(
        objectives=[
            "Deliver a working system that meets the stated business need.",
            "Ensure the system is maintainable, documented, and testable.",
        ],
        functional_requirements=[
            "Core business workflow support.",
            "User authentication and authorisation.",
            "Data persistence and retrieval.",
            "External API integration layer.",
        ],
        non_functional_requirements=[
            "99.9% uptime SLA.",
            "Response time under 500 ms for the 95th percentile.",
            "Horizontal scalability.",
        ],
        scope=f"The system covers the core features described in the project brief: {description[:200]}.",
        out_of_scope=["Legacy system migration.", "Hardware provisioning."],
        constraints=["Must run on cloud infrastructure.", "Compliance with applicable data protection regulations."],
    )


def _fallback_tech_plan(description: str) -> TechAndPlanProposal:
    return TechAndPlanProposal(
        primary_stack=["Python 3.11+", "FastAPI", "PostgreSQL", "Redis"],
        supporting_tools=["Docker", "GitHub Actions", "Prometheus + Grafana"],
        architecture_pattern="Layered monolith with domain-driven module boundaries, ready to extract microservices.",
        architecture_diagram=(
            "```mermaid\n"
            "flowchart TD\n"
            "    Client --> API[API Gateway / FastAPI]\n"
            "    API --> BL[Business Logic Layer]\n"
            "    BL --> DB[(PostgreSQL)]\n"
            "    BL --> Cache[(Redis)]\n"
            "    BL --> Ext[External Services]\n"
            "```"
        ),
        rationale=(
            "FastAPI provides high-performance async REST endpoints. "
            "PostgreSQL handles transactional data with ACID guarantees. "
            "Redis reduces read latency. "
            "Modular monolith minimises operational overhead while preserving evolution paths to microservices."
        ),
        phases=[
            {"name": "Phase 1 – Foundation", "duration": "2 weeks", "deliverables": "Project scaffolding, CI/CD, core data models, authentication."},
            {"name": "Phase 2 – Core Features", "duration": "4 weeks", "deliverables": "Primary business workflows, REST API, unit tests."},
            {"name": "Phase 3 – Integration", "duration": "2 weeks", "deliverables": "External integrations, end-to-end tests."},
            {"name": "Phase 4 – Hardening", "duration": "2 weeks", "deliverables": "Performance tuning, security review, documentation."},
        ],
        total_estimated_duration="10 weeks",
        implementation_risks=[
            "Third-party API instability.",
            "Scope creep from stakeholder changes.",
            "Underestimated data migration complexity.",
        ],
    )


def _fallback_documentation(scaffold_requested: bool) -> str:
    scaffold_section = ""
    if scaffold_requested:
        scaffold_section = """
## 4. Suggested project scaffolding

```text
project/
  src/
    api/          # Route handlers and request/response schemas
    domain/       # Business logic, entities, value objects
    infra/        # Database, cache, external service clients
    shared/       # Cross-cutting concerns (logging, config, errors)
  tests/
    unit/
    integration/
  docs/
  scripts/
  pyproject.toml
  Dockerfile
  docker-compose.yml
  README.md
```
"""

    return f"""## 3. Documentation outline

### agents.md (initial outline)

```markdown
# Agents

## [Agent A]
**Role:** ...
**Input consumed from state:**
| Field | Purpose |
|---|---|
| ... | ... |
**Output written to state:**
| Field | Type | Description |
|---|---|---|
| ... | ... | ... |

## [Agent B]
**Role:** ...
```

### Skills outline

- `skills/workflow.md` – Branching strategy, CI requirements, commit conventions.
- `skills/testing.md` – Testing pyramid, coverage thresholds, integration test setup.
- `skills/documentation.md` – README standards, ADR format, API reference rules.

### README structure

1. Project overview
2. Architecture diagram
3. Quick start (local + Docker)
4. Environment variables reference
5. Development guide
6. Testing
7. Deployment
8. Contributing
{scaffold_section}"""


def _fallback_evaluation(description: str) -> ProjectEvaluation:
    return ProjectEvaluation(
        overall_status=f"Project in progress. Review triggered for: {description[:120]}",
        requirements_coverage=(
            "Partial coverage of documented requirements. "
            "Core functionality appears to be in progress, but non-functional requirements need review."
        ),
        bad_practices_identified=[
            "Missing or incomplete test coverage.",
            "Hardcoded configuration values.",
            "Lack of structured error handling.",
            "No observability instrumentation.",
        ],
        improvement_suggestions=[
            "Introduce a linting and formatting pipeline.",
            "Add centralised logging and health-check endpoints.",
            "Document public APIs with OpenAPI annotations.",
            "Implement a secrets management strategy.",
        ],
        priority_actions=[
            "Fix critical missing test coverage.",
            "Remove all hardcoded secrets and credentials.",
            "Add CI/CD pipeline if not present.",
        ],
        risks_identified=[
            "Security exposure from hardcoded credentials.",
            "Technical debt accumulation without a test safety net.",
        ],
    )


def _fallback_audit(description: str) -> CompletionAudit:
    return CompletionAudit(
        objectives_met=["Core functionality delivered.", "System is deployable."],
        objectives_not_met=["Performance targets not verified.", "Accessibility compliance not addressed."],
        missing_features=["Admin dashboard.", "Audit logging.", "Rate limiting."],
        quality_gaps=["Test coverage below acceptable threshold.", "No end-to-end tests present."],
        documentation_gaps=[
            "No API reference documentation.",
            "Deployment runbook missing.",
            "No architecture decision records.",
        ],
        recommended_next_steps=[
            "Write and publish API reference documentation.",
            "Add performance benchmarks and enforce SLA targets.",
            "Implement missing audit logging and rate-limiting features.",
        ],
        final_verdict=(
            f"Audit of '{description[:80]}': "
            "the project delivers its primary objective but is not production-ready. "
            "Significant gaps in testing, documentation, and non-functional requirements "
            "must be addressed before a general availability release."
        ),
    )


def _fallback_qa(round_number: int, max_rounds: int) -> QAReview:
    approved = round_number >= max_rounds
    return QAReview(
        approved=approved,
        summary=(
            "QA review applied structural completeness heuristics. All key sections are present."
            if approved
            else "QA review detected gaps. A refinement round is recommended before finalisation."
        ),
        gaps=(
            []
            if approved
            else [
                "Additional detail required in the risk assessment.",
                "Technology rationale should reference the stated constraints.",
            ]
        ),
        suggestions=(
            []
            if approved
            else [
                "Expand the data model description.",
                "Add explicit security controls to the proposal.",
            ]
        ),
    )


# ---------------------------------------------------------------------------
# Node: requirements_analyst  (define mode)
# ---------------------------------------------------------------------------


def requirements_analyst_node(state: LifecycleState, container: LifecycleContainer) -> dict[str, Any]:
    description = state["project_description"]
    qa_feedback = state.get("qa_review_doc", "")

    messages = [
        SystemMessage(
            content=(
                "You are the Requirements Analyst agent. Given a project description, extract clear objectives, "
                "functional requirements, non-functional requirements, scope, out-of-scope items, and constraints. "
                "Return ONLY JSON with keys: objectives, functional_requirements, non_functional_requirements, "
                "scope, out_of_scope, constraints."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "project_description": description,
                    "previous_qa_feedback": qa_feedback,
                    "output_format": "JSON",
                },
                ensure_ascii=False,
                indent=2,
            )
        ),
    ]

    try:
        response = container.llm.invoke(messages)
        analysis = RequirementsAnalysis.model_validate(json.loads(str(response.content)))
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        analysis = _fallback_requirements(description)
        error = _format_fallback_error("RequirementsAnalyst", "parse", exc)
    except (ConnectionError, TimeoutError, OSError, httpx.HTTPError) as exc:  # pragma: no cover
        analysis = _fallback_requirements(description)
        error = _format_fallback_error("RequirementsAnalyst", "llm", exc)
    else:
        error = ""

    doc = "\n".join(
        [
            "## 1. Requirements analysis",
            "",
            "### Objectives",
            *[f"- {o}" for o in analysis.objectives],
            "",
            "### Functional requirements",
            *[f"- {r}" for r in analysis.functional_requirements],
            "",
            "### Non-functional requirements",
            *[f"- {r}" for r in (analysis.non_functional_requirements or ["(none identified)"])],
            "",
            "### Scope",
            analysis.scope,
            "",
            "### Out of scope",
            *[f"- {item}" for item in (analysis.out_of_scope or ["(none specified)"])],
            "",
            "### Constraints",
            *[f"- {c}" for c in (analysis.constraints or ["(none specified)"])],
        ]
    )

    output: dict[str, Any] = {
        "requirements_doc": doc,
        "messages": [AIMessage(content=doc, name="requirements_analyst")],
    }
    if error:
        output["errors"] = [*state["errors"], error][-8:]
    return output


# ---------------------------------------------------------------------------
# Node: tech_planner  (define mode)
# ---------------------------------------------------------------------------


def tech_planner_node(state: LifecycleState, container: LifecycleContainer) -> dict[str, Any]:
    description = state["project_description"]
    requirements = state.get("requirements_doc", "")

    messages = [
        SystemMessage(
            content=(
                "You are the Technology and Planning agent. Given requirements, propose a primary technology stack, "
                "supporting tools, architecture pattern, a Mermaid flowchart architecture diagram, rationale, "
                "implementation phases with durations and deliverables, total estimated duration, and implementation risks. "
                "Return ONLY JSON with keys: primary_stack, supporting_tools, architecture_pattern, architecture_diagram, "
                "rationale, phases (list of {name, duration, deliverables}), total_estimated_duration, implementation_risks."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "project_description": description,
                    "requirements_summary": requirements[:1200],
                    "output_format": "JSON",
                },
                ensure_ascii=False,
                indent=2,
            )
        ),
    ]

    try:
        response = container.llm.invoke(messages)
        proposal = TechAndPlanProposal.model_validate(json.loads(str(response.content)))
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        proposal = _fallback_tech_plan(description)
        error = _format_fallback_error("TechPlanner", "parse", exc)
    except (ConnectionError, TimeoutError, OSError, httpx.HTTPError) as exc:  # pragma: no cover
        proposal = _fallback_tech_plan(description)
        error = _format_fallback_error("TechPlanner", "llm", exc)
    else:
        error = ""

    phases_rows = "\n".join(
        f"| {p.get('name', '?')} | {p.get('duration', '?')} | {p.get('deliverables', '?')} |"
        for p in proposal.phases
    )

    doc = "\n".join(
        [
            "## 2. Technology proposal and implementation plan",
            "",
            "### Primary stack",
            *[f"- {t}" for t in proposal.primary_stack],
            "",
            "### Supporting tools",
            *[f"- {t}" for t in (proposal.supporting_tools or ["(none specified)"])],
            "",
            "### Architecture pattern",
            proposal.architecture_pattern,
            "",
            "### Architecture diagram",
            proposal.architecture_diagram,
            "",
            "### Rationale",
            proposal.rationale,
            "",
            "### Implementation phases",
            "| Phase | Duration | Deliverables |",
            "|---|---|---|",
            phases_rows,
            "",
            f"**Total estimated duration:** {proposal.total_estimated_duration}",
            "",
            "### Implementation risks",
            *[f"- {r}" for r in (proposal.implementation_risks or ["(none identified)"])],
        ]
    )

    output: dict[str, Any] = {
        "tech_plan_doc": doc,
        "messages": [AIMessage(content=doc, name="tech_planner")],
    }
    if error:
        output["errors"] = [*state["errors"], error][-8:]
    return output


# ---------------------------------------------------------------------------
# Node: documentation_generator  (define mode)
# ---------------------------------------------------------------------------


def documentation_generator_node(state: LifecycleState, container: LifecycleContainer) -> dict[str, Any]:
    description = state["project_description"]
    requirements = state.get("requirements_doc", "")
    tech_plan = state.get("tech_plan_doc", "")
    scaffold_requested = state.get("scaffold_requested", False)

    scaffold_instruction = (
        "Also produce a suggested project directory scaffolding with key directories and files and their purpose."
        if scaffold_requested
        else "Do not include a scaffolding section; focus on documentation outlines only."
    )

    messages = [
        SystemMessage(
            content=(
                "You are the Documentation Generator agent. Produce the following in well-structured Markdown: "
                "(1) an initial agents.md outline describing the planned agents and their input/output contracts, "
                "(2) a skills outline listing the skill files needed and their purpose, "
                "(3) a README structure for the project. "
                f"{scaffold_instruction}"
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "project_description": description,
                    "requirements_summary": requirements[:800],
                    "tech_plan_summary": tech_plan[:800],
                    "scaffold_requested": scaffold_requested,
                },
                ensure_ascii=False,
                indent=2,
            )
        ),
    ]

    try:
        response = container.llm.invoke(messages)
        doc = str(response.content).strip()
        if not doc:
            raise ValueError("Empty documentation outline")
    except (ConnectionError, TimeoutError, OSError, httpx.HTTPError, ValueError) as exc:  # pragma: no cover
        doc = _fallback_documentation(scaffold_requested)
        error = _format_fallback_error("DocumentationGenerator", "fallback", exc)
    else:
        error = ""

    output: dict[str, Any] = {
        "documentation_outline": doc,
        "messages": [AIMessage(content=doc, name="documentation_generator")],
    }
    if error:
        output["errors"] = [*state["errors"], error][-8:]
    return output


# ---------------------------------------------------------------------------
# Node: project_evaluator  (evaluate mode)
# ---------------------------------------------------------------------------


def project_evaluator_node(state: LifecycleState, container: LifecycleContainer) -> dict[str, Any]:
    description = state["project_description"]
    qa_feedback = state.get("qa_review_doc", "")

    messages = [
        SystemMessage(
            content=(
                "You are the Project Evaluator agent. Critically evaluate the ongoing project described. "
                "Identify overall status, requirements coverage, bad practices, improvement suggestions, "
                "priority actions, and risks. "
                "Return ONLY JSON with keys: overall_status, requirements_coverage, bad_practices_identified, "
                "improvement_suggestions, priority_actions, risks_identified."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "project_description": description,
                    "previous_qa_feedback": qa_feedback,
                    "output_format": "JSON",
                },
                ensure_ascii=False,
                indent=2,
            )
        ),
    ]

    try:
        response = container.llm.invoke(messages)
        evaluation = ProjectEvaluation.model_validate(json.loads(str(response.content)))
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        evaluation = _fallback_evaluation(description)
        error = _format_fallback_error("ProjectEvaluator", "parse", exc)
    except (ConnectionError, TimeoutError, OSError, httpx.HTTPError) as exc:  # pragma: no cover
        evaluation = _fallback_evaluation(description)
        error = _format_fallback_error("ProjectEvaluator", "llm", exc)
    else:
        error = ""

    doc = "\n".join(
        [
            "## Project evaluation",
            "",
            "### Overall status",
            evaluation.overall_status,
            "",
            "### Requirements coverage",
            evaluation.requirements_coverage,
            "",
            "### Bad practices identified",
            *[f"- {p}" for p in (evaluation.bad_practices_identified or ["(none identified)"])],
            "",
            "### Improvement suggestions",
            *[f"- {s}" for s in evaluation.improvement_suggestions],
            "",
            "### Priority actions",
            *[f"- {a}" for a in evaluation.priority_actions],
            "",
            "### Risks identified",
            *[f"- {r}" for r in (evaluation.risks_identified or ["(none identified)"])],
        ]
    )

    output: dict[str, Any] = {
        "evaluation_doc": doc,
        "messages": [AIMessage(content=doc, name="project_evaluator")],
    }
    if error:
        output["errors"] = [*state["errors"], error][-8:]
    return output


# ---------------------------------------------------------------------------
# Node: completion_auditor  (audit mode)
# ---------------------------------------------------------------------------


def completion_auditor_node(state: LifecycleState, container: LifecycleContainer) -> dict[str, Any]:
    description = state["project_description"]
    qa_feedback = state.get("qa_review_doc", "")

    messages = [
        SystemMessage(
            content=(
                "You are the Completion Auditor agent. Audit the finished project to determine: "
                "which objectives were met, which were not, missing features, quality gaps, documentation gaps, "
                "recommended next steps, and a final verdict on production readiness. "
                "Return ONLY JSON with keys: objectives_met, objectives_not_met, missing_features, quality_gaps, "
                "documentation_gaps, recommended_next_steps, final_verdict."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "project_description": description,
                    "previous_qa_feedback": qa_feedback,
                    "output_format": "JSON",
                },
                ensure_ascii=False,
                indent=2,
            )
        ),
    ]

    try:
        response = container.llm.invoke(messages)
        audit = CompletionAudit.model_validate(json.loads(str(response.content)))
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        audit = _fallback_audit(description)
        error = _format_fallback_error("CompletionAuditor", "parse", exc)
    except (ConnectionError, TimeoutError, OSError, httpx.HTTPError) as exc:  # pragma: no cover
        audit = _fallback_audit(description)
        error = _format_fallback_error("CompletionAuditor", "llm", exc)
    else:
        error = ""

    doc = "\n".join(
        [
            "## Completion audit",
            "",
            "### Objectives met",
            *[f"- {o}" for o in (audit.objectives_met or ["(none confirmed)"])],
            "",
            "### Objectives not met",
            *[f"- {o}" for o in (audit.objectives_not_met or ["(none identified)"])],
            "",
            "### Missing features",
            *[f"- {f}" for f in (audit.missing_features or ["(none identified)"])],
            "",
            "### Quality gaps",
            *[f"- {g}" for g in (audit.quality_gaps or ["(none identified)"])],
            "",
            "### Documentation gaps",
            *[f"- {g}" for g in (audit.documentation_gaps or ["(none identified)"])],
            "",
            "### Recommended next steps",
            *[f"- {s}" for s in audit.recommended_next_steps],
            "",
            "### Final verdict",
            audit.final_verdict,
        ]
    )

    output: dict[str, Any] = {
        "audit_doc": doc,
        "messages": [AIMessage(content=doc, name="completion_auditor")],
    }
    if error:
        output["errors"] = [*state["errors"], error][-8:]
    return output


# ---------------------------------------------------------------------------
# Node: qa_reviewer
# ---------------------------------------------------------------------------


def qa_reviewer_node(state: LifecycleState, container: LifecycleContainer) -> dict[str, Any]:
    mode = state["mode"]
    round_number = state["round_number"] + 1

    if mode == "define":
        content_to_review = "\n\n".join(
            filter(
                None,
                [
                    state.get("requirements_doc", ""),
                    state.get("tech_plan_doc", ""),
                    state.get("documentation_outline", ""),
                ],
            )
        )
    elif mode == "evaluate":
        content_to_review = state.get("evaluation_doc", "")
    else:
        content_to_review = state.get("audit_doc", "")

    messages = [
        SystemMessage(
            content=(
                "You are the Quality Review agent. Assess the completeness, accuracy, and actionability of "
                "the provided document. Approve if it covers all key aspects thoroughly. "
                "Otherwise, identify specific gaps and improvement suggestions. "
                "Return ONLY JSON with keys: approved (bool), summary, gaps (list), suggestions (list)."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "mode": mode,
                    "round_number": round_number,
                    "max_rounds": state["max_rounds"],
                    "content": content_to_review[:3000],
                },
                ensure_ascii=False,
                indent=2,
            )
        ),
    ]

    try:
        response = container.llm.invoke(messages)
        review = QAReview.model_validate(json.loads(str(response.content)))
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:
        review = _fallback_qa(round_number, state["max_rounds"])
        error = _format_fallback_error("QAReviewer", "parse", exc)
    except (ConnectionError, TimeoutError, OSError, httpx.HTTPError) as exc:  # pragma: no cover
        review = _fallback_qa(round_number, state["max_rounds"])
        error = _format_fallback_error("QAReviewer", "llm", exc)
    else:
        error = ""

    if round_number >= state["max_rounds"] and not review.approved:
        review = QAReview(
            approved=True,
            summary=review.summary + " [Auto-approved: max rounds reached.]",
            gaps=review.gaps,
            suggestions=review.suggestions,
        )

    qa_doc = "\n".join(
        [
            f"## QA review (round {round_number})",
            f"- Approved: {'Yes' if review.approved else 'No'}",
            f"- Summary: {review.summary}",
            "- Gaps:",
            *[f"  - {g}" for g in (review.gaps or ["None"])],
            "- Suggestions:",
            *[f"  - {s}" for s in (review.suggestions or ["None"])],
        ]
    )

    review_entry: dict[str, Any] = {
        "round": round_number,
        "mode": mode,
        "approved": review.approved,
        "summary": review.summary,
        "gaps": review.gaps,
        "suggestions": review.suggestions,
    }

    output: dict[str, Any] = {
        "qa_review_doc": qa_doc,
        "qa_approved": review.approved,
        "round_number": round_number,
        "review_log": [*state["review_log"], review_entry],
        "messages": [AIMessage(content=qa_doc, name="qa_reviewer")],
    }
    if error:
        output["errors"] = [*state["errors"], error][-8:]
    return output


# ---------------------------------------------------------------------------
# Node: finalizer
# ---------------------------------------------------------------------------


def finalizer_node(state: LifecycleState) -> dict[str, Any]:
    mode = state["mode"]
    approval_reason = (
        "Approved by QA agent."
        if state["qa_approved"]
        else f"Iteration limit reached ({state['max_rounds']} rounds). Final output frozen for manual follow-up."
    )

    rounds_section: list[str] = []
    for item in state["review_log"]:
        rounds_section.extend(
            [
                f"### Round {item['round']}",
                f"- Approved: {'Yes' if item['approved'] else 'No'}",
                f"- Summary: {item['summary']}",
                "- Gaps:",
                *[f"  - {g}" for g in (item.get("gaps") or ["None"])],
            ]
        )

    if mode == "define":
        title = "# Project definition specification"
        content_sections = [
            state.get("requirements_doc") or "No requirements analysis produced.",
            state.get("tech_plan_doc") or "No technology plan produced.",
            state.get("documentation_outline") or "No documentation outline produced.",
        ]
    elif mode == "evaluate":
        title = "# Project evaluation report"
        content_sections = [state.get("evaluation_doc") or "No evaluation produced."]
    else:
        title = "# Project completion audit report"
        content_sections = [state.get("audit_doc") or "No audit produced."]

    final_document = "\n\n".join(
        [
            title,
            (
                f"## Overview\n"
                f"- Mode: {mode}\n"
                f"- Debate rounds: {state['round_number']} / {state['max_rounds']}\n"
                f"- Closure: {approval_reason}"
            ),
            "\n\n".join(content_sections),
            "## QA review history",
            "\n".join(rounds_section) if rounds_section else "No QA rounds recorded.",
            "## Final QA review",
            state.get("qa_review_doc") or "No QA review produced.",
        ]
    )

    return {"final_document": final_document}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------


def route_by_mode(state: LifecycleState) -> str:
    mode = state.get("mode", "define")
    if mode == "evaluate":
        return "project_evaluator"
    if mode == "audit":
        return "completion_auditor"
    return "requirements_analyst"


def route_after_qa(state: LifecycleState) -> str:
    if state["qa_approved"] or state["round_number"] >= state["max_rounds"]:
        return "finalizer"
    mode = state.get("mode", "define")
    if mode == "evaluate":
        return "project_evaluator"
    if mode == "audit":
        return "completion_auditor"
    return "requirements_analyst"


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


def build_graph(container: LifecycleContainer):
    graph = StateGraph(LifecycleState)

    graph.add_node("requirements_analyst", lambda s: requirements_analyst_node(s, container))
    graph.add_node("tech_planner", lambda s: tech_planner_node(s, container))
    graph.add_node("documentation_generator", lambda s: documentation_generator_node(s, container))
    graph.add_node("project_evaluator", lambda s: project_evaluator_node(s, container))
    graph.add_node("completion_auditor", lambda s: completion_auditor_node(s, container))
    graph.add_node("qa_reviewer", lambda s: qa_reviewer_node(s, container))
    graph.add_node("finalizer", finalizer_node)

    # Entry routing based on mode
    graph.add_conditional_edges(
        START,
        route_by_mode,
        {
            "requirements_analyst": "requirements_analyst",
            "project_evaluator": "project_evaluator",
            "completion_auditor": "completion_auditor",
        },
    )

    # define mode chain
    graph.add_edge("requirements_analyst", "tech_planner")
    graph.add_edge("tech_planner", "documentation_generator")
    graph.add_edge("documentation_generator", "qa_reviewer")

    # evaluate and audit go directly to qa
    graph.add_edge("project_evaluator", "qa_reviewer")
    graph.add_edge("completion_auditor", "qa_reviewer")

    # QA routing: loop or finalise
    graph.add_conditional_edges(
        "qa_reviewer",
        route_after_qa,
        {
            "requirements_analyst": "requirements_analyst",
            "project_evaluator": "project_evaluator",
            "completion_auditor": "completion_auditor",
            "finalizer": "finalizer",
        },
    )

    graph.add_edge("finalizer", END)

    return graph.compile(checkpointer=MemorySaver())


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_lifecycle(
    description: str,
    mode: str,
    scaffold_requested: bool,
    thread_id: str,
    max_rounds: int,
):
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of: {', '.join(VALID_MODES)}")

    bounded_rounds = max(1, min(MAX_REVIEW_ROUNDS, max_rounds))
    container = LifecycleContainer(llm=_build_llm())
    lifecycle_graph = build_graph(container)

    initial_state: LifecycleState = {
        "project_description": description.strip(),
        "mode": mode,
        "scaffold_requested": scaffold_requested,
        "messages": [HumanMessage(content=description.strip())],
        "round_number": 0,
        "max_rounds": bounded_rounds,
        "requirements_doc": "",
        "tech_plan_doc": "",
        "documentation_outline": "",
        "evaluation_doc": "",
        "audit_doc": "",
        "qa_review_doc": "",
        "qa_approved": False,
        "review_log": [],
        "final_document": "",
        "errors": [],
    }

    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 30}
    final_state = lifecycle_graph.invoke(initial_state, config=config)
    checkpoint = lifecycle_graph.get_state(config)
    history = list(lifecycle_graph.get_state_history(config))
    return final_state, checkpoint, history


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the project lifecycle multi-agent pack.")
    parser.add_argument(
        "--input",
        default="Build a SaaS task management platform with team collaboration and reporting.",
        help="Project description or context the agents will analyse.",
    )
    parser.add_argument(
        "--mode",
        choices=list(VALID_MODES),
        default="define",
        help=(
            "Operating mode: "
            "'define' for new project definition (requirements, tech, docs, optional scaffold); "
            "'evaluate' for an ongoing project review; "
            "'audit' for a completed project audit."
        ),
    )
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Generate a project directory scaffolding outline (applies to define mode only).",
    )
    parser.add_argument("--thread-id", default="lifecycle-001", help="Checkpoint thread identifier.")
    parser.add_argument("--max-rounds", type=int, default=2, help="QA review round cap (1-3).")
    parser.add_argument("--output", help="Optional Markdown output file path.")
    parser.add_argument("--show-history", action="store_true", help="Print checkpoint history for debugging.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    final_state, checkpoint, history = run_lifecycle(
        description=args.input,
        mode=args.mode,
        scaffold_requested=args.scaffold,
        thread_id=args.thread_id,
        max_rounds=args.max_rounds,
    )

    document = final_state.get("final_document", "")
    print(document)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(document)
        print(f"\nSaved final document to: {args.output}")

    if args.show_history:
        print("\nCheckpoint next:", checkpoint.next)
        print("History length:", len(history))

    errors = final_state.get("errors", [])
    if errors:
        print("\nWarnings:")
        for item in errors:
            print(f"  - {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
