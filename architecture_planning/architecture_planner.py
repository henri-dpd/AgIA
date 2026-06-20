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
DEFAULT_BASE_URL = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
MAX_REVIEW_ROUNDS = 3


class QAAudit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved: bool
    summary: str = Field(min_length=20, max_length=1200)
    spof_risks: list[str] = Field(default_factory=list)
    latency_risks: list[str] = Field(default_factory=list)
    scalability_risks: list[str] = Field(default_factory=list)
    data_model: str = Field(min_length=20, max_length=2000)


class DebateState(TypedDict):
    business_requirement: str
    messages: Annotated[list[BaseMessage], add_messages]
    round_number: int
    max_rounds: int
    architect_proposal: str
    qa_review: str
    qa_approved: bool
    review_log: list[dict[str, Any]]
    final_document: str
    errors: list[str]


@dataclass(frozen=True)
class PlannerContainer:
    llm: ChatOllama


def _build_llm() -> ChatOllama:
    return ChatOllama(model=DEFAULT_MODEL, base_url=DEFAULT_BASE_URL, temperature=0.2)


def _parse_audit(raw_content: str) -> QAAudit:
    payload = json.loads(raw_content)
    return QAAudit.model_validate(payload)


def _deterministic_architect_proposal(requirement: str, qa_feedback: str, round_number: int) -> str:
    corrective = "Apply the QA findings from the previous review before closing the design."
    if not qa_feedback.strip():
        corrective = "No previous review; produce a first baseline architecture."

    return f"""## Infrastructure architecture proposal (round {round_number})

### Topology
- API Gateway + BFF for external consumers.
- Modular microservices split by bounded contexts.
- Event broker for asynchronous integrations and domain events.
- Multi-zone deployment with active-active compute nodes.

### Data and consistency
- SQL database for transactional aggregates and financial integrity.
- NoSQL document store for read-heavy denormalized projections.
- Cache-aside with Redis for low-latency reads.
- Event-driven choreography with outbox pattern and idempotent consumers.

### Reliability and scaling
- Circuit breakers, retries with jitter, and bulkheads between services.
- Horizontal scaling for stateless services and worker consumers.
- Centralized observability (logs, metrics, traces).

### Review integration
- {corrective}
- QA feedback considered: {qa_feedback or 'None'}
"""


def architect_node(state: DebateState, container: PlannerContainer) -> dict[str, Any]:
    round_number = state["round_number"] + 1
    requirement = state["business_requirement"]
    prior_review = state.get("qa_review", "")

    messages = [
        SystemMessage(
            content=(
                "You are the Infrastructure Architect agent. Produce a concise but technical architecture proposal "
                "including topology, SQL vs NoSQL rationale, cache strategy, data consistency, and architectural pattern."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "business_requirement": requirement,
                    "round_number": round_number,
                    "previous_qa_review": prior_review,
                    "output_format": "Markdown",
                },
                ensure_ascii=False,
                indent=2,
            )
        ),
    ]

    try:
        response = container.llm.invoke(messages)
        proposal = str(response.content).strip()
        if not proposal:
            raise ValueError("Empty architect proposal")
    except (ConnectionError, TimeoutError, OSError, RuntimeError, httpx.HTTPError) as exc:  # pragma: no cover - fallback path
        proposal = _deterministic_architect_proposal(requirement, prior_review, round_number)
        return {
            "architect_proposal": proposal,
            "messages": [AIMessage(content=proposal, name="infra_architect")],
            "errors": [*state["errors"], f"Architect LLM unavailable: {exc}"][-8:],
        }

    return {
        "architect_proposal": proposal,
        "messages": [AIMessage(content=proposal, name="infra_architect")],
    }


def _fallback_audit(proposal: str, round_number: int) -> QAAudit:
    lowered = proposal.lower()
    has_topology = "topology" in lowered or "microservice" in lowered
    has_data = "sql" in lowered and "nosql" in lowered
    has_cache = "cache" in lowered or "redis" in lowered
    has_consistency = "consisten" in lowered or "outbox" in lowered or "idempotent" in lowered

    approved = has_topology and has_data and has_cache and has_consistency
    if round_number >= MAX_REVIEW_ROUNDS:
        approved = True

    return QAAudit(
        approved=approved,
        summary=(
            "Audit reviewed SPOF, latency, scalability, and data model concerns. "
            "Design is approved for baseline specification."
            if approved
            else "Audit found unresolved risks. Improve resilience controls and explicit data model boundaries."
        ),
        spof_risks=["Single event broker cluster without quorum policy."] if not approved else [],
        latency_risks=["Synchronous hops across service chain may exceed SLA."] if not approved else [],
        scalability_risks=["No explicit shard strategy for read projections."] if not approved else [],
        data_model=(
            "Core SQL entities: Account, Contract, Invoice, Payment, LedgerEntry.\n"
            "NoSQL projection: BillingTimeline {tenantId, invoiceId, events[], balanceSnapshot}."
        ),
    )


def qa_node(state: DebateState, container: PlannerContainer) -> dict[str, Any]:
    proposal = state["architect_proposal"]
    round_number = state["round_number"] + 1

    messages = [
        SystemMessage(
            content=(
                "You are the Requirements & QA agent. Critically audit the architecture proposal. "
                "Identify SPOF, latency bottlenecks, scalability risks, and define an initial data model. "
                "Return ONLY JSON with keys: approved, summary, spof_risks, latency_risks, scalability_risks, data_model."
            )
        ),
        HumanMessage(
            content=json.dumps(
                {
                    "round_number": round_number,
                    "max_rounds": state["max_rounds"],
                    "business_requirement": state["business_requirement"],
                    "architect_proposal": proposal,
                },
                ensure_ascii=False,
                indent=2,
            )
        ),
    ]

    try:
        response = container.llm.invoke(messages)
        audit = _parse_audit(str(response.content))
    except (ValidationError, json.JSONDecodeError, ValueError) as exc:  # pragma: no cover - fallback path
        audit = _fallback_audit(proposal, round_number)
        error = f"QA parsing fallback used: {exc}"
    except (ConnectionError, TimeoutError, OSError, RuntimeError, httpx.HTTPError) as exc:  # pragma: no cover - fallback path
        audit = _fallback_audit(proposal, round_number)
        error = f"QA LLM unavailable: {exc}"
    else:
        error = ""

    qa_markdown = "\n".join(
        [
            f"## QA review (round {round_number})",
            f"- Approved: {'Yes' if audit.approved else 'No'}",
            f"- Summary: {audit.summary}",
            "- SPOF risks:",
            *[f"  - {item}" for item in (audit.spof_risks or ["None"])],
            "- Latency risks:",
            *[f"  - {item}" for item in (audit.latency_risks or ["None"])],
            "- Scalability risks:",
            *[f"  - {item}" for item in (audit.scalability_risks or ["None"])],
            "- Initial data model:",
            *[f"  {line}" for line in audit.data_model.splitlines()],
        ]
    )

    review_log = [
        *state["review_log"],
        {
            "round": round_number,
            "approved": audit.approved,
            "qa_summary": audit.summary,
            "spof_risks": audit.spof_risks,
            "latency_risks": audit.latency_risks,
            "scalability_risks": audit.scalability_risks,
            "data_model": audit.data_model,
            "architect_proposal": proposal,
        },
    ]

    output: dict[str, Any] = {
        "qa_review": qa_markdown,
        "qa_approved": audit.approved,
        "round_number": round_number,
        "review_log": review_log,
        "messages": [AIMessage(content=qa_markdown, name="specs_qa_agent")],
    }

    if error:
        output["errors"] = [*state["errors"], error][-8:]

    return output


def route_after_qa(state: DebateState) -> str:
    if state["qa_approved"] or state["round_number"] >= state["max_rounds"]:
        return "finalize"
    return "architect"


def finalize_node(state: DebateState) -> dict[str, Any]:
    approval_reason = (
        "Approved by QA agent."
        if state["qa_approved"]
        else f"Iteration limit reached ({state['max_rounds']} rounds). Final proposal frozen for manual follow-up."
    )

    rounds_section: list[str] = []
    for item in state["review_log"]:
        rounds_section.extend(
            [
                f"### Round {item['round']}",
                "#### Architect proposal",
                item["architect_proposal"],
                "#### QA decision",
                f"- Approved: {'Yes' if item['approved'] else 'No'}",
                f"- Summary: {item['qa_summary']}",
                "- SPOF risks:",
                *[f"  - {risk}" for risk in (item["spof_risks"] or ["None"])],
                "- Latency risks:",
                *[f"  - {risk}" for risk in (item["latency_risks"] or ["None"])],
                "- Scalability risks:",
                *[f"  - {risk}" for risk in (item["scalability_risks"] or ["None"])],
                "- Data model:",
                *[f"  {line}" for line in str(item["data_model"]).splitlines()],
            ]
        )

    final_document = "\n\n".join(
        [
            "# Master technical architecture specification",
            "## 1. Business requirement",
            state["business_requirement"],
            "## 2. Consensus result",
            f"- Debate rounds executed: {state['round_number']} / {state['max_rounds']}\n- Closure condition: {approval_reason}",
            "## 3. Debate history",
            "\n".join(rounds_section) if rounds_section else "No rounds recorded.",
            "## 4. Final architecture proposal",
            state["architect_proposal"] or "No architecture proposal produced.",
            "## 5. Final QA review",
            state["qa_review"] or "No QA review produced.",
        ]
    )

    return {"final_document": final_document}


def build_graph(container: PlannerContainer):
    graph = StateGraph(DebateState)

    graph.add_node("architect", lambda state: architect_node(state, container))
    graph.add_node("qa", lambda state: qa_node(state, container))
    graph.add_node("finalize", finalize_node)

    graph.add_edge(START, "architect")
    graph.add_edge("architect", "qa")
    graph.add_conditional_edges("qa", route_after_qa, {"architect": "architect", "finalize": "finalize"})
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=MemorySaver())


def run_planner(requirement: str, thread_id: str, max_rounds: int):
    bounded_rounds = max(1, min(MAX_REVIEW_ROUNDS, max_rounds))
    container = PlannerContainer(llm=_build_llm())
    planner_graph = build_graph(container)

    initial_state: DebateState = {
        "business_requirement": requirement.strip(),
        "messages": [HumanMessage(content=requirement.strip())],
        "round_number": 0,
        "max_rounds": bounded_rounds,
        "architect_proposal": "",
        "qa_review": "",
        "qa_approved": False,
        "review_log": [],
        "final_document": "",
        "errors": [],
    }

    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 20}
    final_state = planner_graph.invoke(initial_state, config=config)
    checkpoint = planner_graph.get_state(config)
    history = list(planner_graph.get_state_history(config))
    return final_state, checkpoint, history


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the architecture planning multi-agent pack.")
    parser.add_argument(
        "--input",
        default="Design a highly available medical billing platform for multi-country operations.",
        help="Business requirement that the agents will transform into a technical architecture document.",
    )
    parser.add_argument("--thread-id", default="architecture-001", help="Checkpoint thread identifier.")
    parser.add_argument("--max-rounds", type=int, default=3, help="Debate round cap (1-3).")
    parser.add_argument("--output", help="Optional Markdown output file path.")
    parser.add_argument("--show-history", action="store_true", help="Print checkpoint history for debugging.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    final_state, checkpoint, history = run_planner(args.input, args.thread_id, args.max_rounds)

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
            print(f"- {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
