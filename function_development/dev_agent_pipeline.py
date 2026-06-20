from __future__ import annotations

import argparse
import ast
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Final, Literal, Protocol, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field, ValidationError

LOGGER = logging.getLogger("agia.function_development")
DEFAULT_MODEL: Final[str] = os.getenv("OLLAMA_MODEL", "llama3.1")
DEFAULT_BASE_URL: Final[str] = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
DEFAULT_THREAD_ID: Final[str] = "function-dev-001"
RECURSION_LIMIT: Final[int] = 25
MAX_CORRECTION_ROUNDS: Final[int] = 4
MAX_PLANNER_ROUNDS: Final[int] = 2
PYTEST_TIMEOUT_SECONDS: Final[int] = 30
SPEC_MAX_LENGTH: Final[int] = 6_000
STACKS_DIR: Final[Path] = Path(__file__).parent / "stacks"
DEFAULT_SPEC: Final[str] = (
    "Implement `def normalize_scores(values: list[float]) -> list[float]` that returns values scaled into the "
    "[0.0, 1.0] range. Preserve the input order, reject an empty list with ValueError, and reject a list where "
    "all values are equal with ValueError."
)
CODE_BLOCK_RE: Final[re.Pattern[str]] = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
JSON_BLOCK_RE: Final[re.Pattern[str]] = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
SIGNATURE_RE: Final[re.Pattern[str]] = re.compile(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
BLOCKED_IMPORTS: Final[frozenset[str]] = frozenset({"os", "subprocess", "socket", "httpx", "requests"})
BLOCKED_CALLS: Final[frozenset[str]] = frozenset(
    {
        "eval",
        "exec",
        "compile",
        "__import__",
        "breakpoint",
        "os.system",
        "os.popen",
        "subprocess.run",
        "subprocess.Popen",
        "subprocess.call",
        "subprocess.check_call",
        "subprocess.check_output",
    }
)


class FunctionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    specification: str = Field(min_length=20, max_length=SPEC_MAX_LENGTH)
    function_name: str = Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")


class GeneratedArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    function_name: str = Field(pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    function_code: str = Field(min_length=20)
    test_code: str = Field(min_length=20)


class ValidationReport(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    success: bool
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    feedback: str | None = None
    blocked_reason: str | None = None


class PlanArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=200)
    context_summary: str = Field(min_length=10, max_length=2000)
    stack_guidelines_applied: list[str] = Field(default_factory=list)
    specifications: str = Field(min_length=20, max_length=SPEC_MAX_LENGTH)
    acceptance_criteria: list[str] = Field(min_length=1)
    documentation: str = Field(min_length=10, max_length=3000)


class ContractReport(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    success: bool
    checked_criteria: list[str] = Field(default_factory=list)
    failed_criteria: list[str] = Field(default_factory=list)
    feedback: str | None = None


class AuditReport(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    approved: bool
    best_practices_violations: list[str] = Field(default_factory=list)
    scope_violations: list[str] = Field(default_factory=list)
    requires_user_action: bool = False
    user_action_description: str | None = None
    requires_plan_rework: bool = False
    feedback: str | None = None


class AgentState(TypedDict):
    request: dict[str, Any]
    stack: str | None
    messages: Annotated[list[BaseMessage], add_messages]
    attempt: int
    planner_attempts: int
    plan_artifact: dict[str, Any] | None
    artifact: dict[str, Any] | None
    validation_report: dict[str, Any] | None
    contract_report: dict[str, Any] | None
    audit_report: dict[str, Any] | None
    status: Literal["queued", "planning", "drafted", "retrying", "validating", "auditing", "completed", "failed"]


class PlannerPort(Protocol):
    def plan(self, request: FunctionRequest, stack_context: str, audit_feedback: str | None) -> PlanArtifact:
        ...


class CoderPort(Protocol):
    def generate(self, request: FunctionRequest, attempt: int, feedback: str | None) -> GeneratedArtifact:
        ...


class TesterPort(Protocol):
    def validate(self, artifact: GeneratedArtifact) -> ValidationReport:
        ...


class ContractValidatorPort(Protocol):
    def validate_contract(self, plan: PlanArtifact, artifact: GeneratedArtifact) -> ContractReport:
        ...


class AuditorPort(Protocol):
    def audit(
        self,
        plan: PlanArtifact,
        artifact: GeneratedArtifact,
        contract: ContractReport,
        attempt: int,
    ) -> AuditReport:
        ...


@dataclass(frozen=True)
class PipelineServices:
    coder: CoderPort
    tester: TesterPort
    planner: PlannerPort = field(default_factory=lambda: PassthroughPlanner())
    contract_validator: ContractValidatorPort = field(default_factory=lambda: PassthroughContractValidator())
    auditor: AuditorPort = field(default_factory=lambda: PassthroughAuditor())


class SecurityViolationError(ValueError):
    pass


class SecurityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[str] = []
        self._aliases: dict[str, str] = {}

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".", 1)[0]
            if root in BLOCKED_IMPORTS:
                self.violations.append(f"Blocked import detected: {alias.name}")
            self._aliases[alias.asname or root] = alias.name
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        root = module.split(".", 1)[0]
        if root in BLOCKED_IMPORTS:
            self.violations.append(f"Blocked import detected: {module}")
        for alias in node.names:
            if module:
                self._aliases[alias.asname or alias.name] = f"{module}.{alias.name}"
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = self._resolve_name(node.func)
        if name in BLOCKED_CALLS:
            self.violations.append(f"Blocked call detected: {name}")
        self.generic_visit(node)

    def _resolve_name(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return self._aliases.get(node.id, node.id)
        if isinstance(node, ast.Attribute):
            parent = self._resolve_name(node.value)
            if parent is None:
                return node.attr
            return f"{parent}.{node.attr}"
        return None


class SecurityValidator:
    def validate(self, label: str, source: str) -> None:
        try:
            tree = ast.parse(source)
        except SyntaxError as exc:
            raise SecurityViolationError(f"{label} is not valid Python: {exc}") from exc

        visitor = SecurityVisitor()
        visitor.visit(tree)
        if visitor.violations:
            details = "; ".join(visitor.violations)
            raise SecurityViolationError(f"{label} failed security validation: {details}")


class PytestExecutionTool:
    def __init__(self, timeout_seconds: int = PYTEST_TIMEOUT_SECONDS) -> None:
        self._timeout_seconds = timeout_seconds

    def run(self, artifact: GeneratedArtifact) -> ValidationReport:
        with tempfile.TemporaryDirectory(prefix="agia-function-dev-") as workspace:
            workspace_path = Path(workspace)
            subject_path = workspace_path / "subject.py"
            test_path = workspace_path / "test_subject.py"

            subject_path.write_text(artifact.function_code, encoding="utf-8")
            test_path.write_text(artifact.test_code, encoding="utf-8")

            command = [sys.executable, "-m", "pytest", "test_subject.py", "-q", "--maxfail=1"]
            completed = subprocess.run(
                command,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
                check=False,
            )

            stdout = completed.stdout.strip()
            stderr = completed.stderr.strip()
            if completed.returncode == 0:
                return ValidationReport(success=True, exit_code=0, stdout=stdout, stderr=stderr)

            feedback_parts = ["Pytest reported at least one failure."]
            if stdout:
                feedback_parts.append(f"STDOUT:\n{stdout}")
            if stderr:
                feedback_parts.append(f"STDERR:\n{stderr}")
            return ValidationReport(
                success=False,
                exit_code=completed.returncode,
                stdout=stdout,
                stderr=stderr,
                feedback="\n\n".join(feedback_parts),
            )


class TesterAgent(TesterPort):
    def __init__(
        self,
        execution_tool: PytestExecutionTool | None = None,
        security_validator: SecurityValidator | None = None,
    ) -> None:
        self._execution_tool = execution_tool or PytestExecutionTool()
        self._security_validator = security_validator or SecurityValidator()

    def validate(self, artifact: GeneratedArtifact) -> ValidationReport:
        try:
            self._security_validator.validate("Generated function", artifact.function_code)
            self._security_validator.validate("Generated tests", artifact.test_code)
        except SecurityViolationError as exc:
            return ValidationReport(success=False, blocked_reason=str(exc), feedback=str(exc))

        return self._execution_tool.run(artifact)


def load_stack_context(stack: str | None) -> str:
    """Read best_practices, workflow, and skills files for the given stack."""
    if not stack:
        return ""
    stack_dir = STACKS_DIR / stack.lower().replace(" ", "-")
    if not stack_dir.is_dir():
        LOGGER.warning("No stack guidelines found for: %s", stack)
        return f"No guidelines found for stack: {stack}"
    parts: list[str] = []
    for file_name in ("best_practices.md", "workflow.md", "skills.md"):
        file_path = stack_dir / file_name
        if file_path.exists():
            parts.append(f"### {file_name}\n{file_path.read_text(encoding='utf-8')}")
    return "\n\n".join(parts)


def _extract_json(text: str) -> dict[str, Any] | None:
    """Extract the first JSON object from an LLM response."""
    fence_match = JSON_BLOCK_RE.search(text)
    candidate = fence_match.group(1) if fence_match else text
    brace_match = re.search(r"\{.*\}", candidate, re.DOTALL)
    if not brace_match:
        return None
    try:
        return json.loads(brace_match.group())
    except json.JSONDecodeError:
        return None


class PassthroughPlanner:
    """Non-LLM planner that forwards the specification directly."""

    def plan(self, request: FunctionRequest, stack_context: str, audit_feedback: str | None) -> PlanArtifact:
        specs = request.specification
        if audit_feedback:
            specs = f"{specs}\n\nAudit feedback to address:\n{audit_feedback}"
        applied = [stack_context[:60]] if stack_context else []
        return PlanArtifact(
            title=f"Plan for {request.function_name}",
            context_summary=request.specification[:200],
            stack_guidelines_applied=applied,
            specifications=specs[:SPEC_MAX_LENGTH],
            acceptance_criteria=["Function must be implemented as specified.", "All tests must pass."],
            documentation=f"`{request.function_name}` implemented per specification.",
        )


class PassthroughContractValidator:
    """Non-LLM contract validator that always approves."""

    def validate_contract(self, plan: PlanArtifact, artifact: GeneratedArtifact) -> ContractReport:
        return ContractReport(
            success=True,
            checked_criteria=list(plan.acceptance_criteria),
            failed_criteria=[],
            feedback=None,
        )


class PassthroughAuditor:
    """Non-LLM auditor that approves when the contract passes."""

    def audit(
        self,
        plan: PlanArtifact,
        artifact: GeneratedArtifact,
        contract: ContractReport,
        attempt: int,
    ) -> AuditReport:
        return AuditReport(
            approved=contract.success,
            best_practices_violations=[],
            scope_violations=[],
            requires_user_action=False,
            user_action_description=None,
            requires_plan_rework=False,
            feedback=None,
        )


class OllamaPlanner(PlannerPort):
    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL) -> None:
        self._model = model
        self._base_url = base_url

    def plan(self, request: FunctionRequest, stack_context: str, audit_feedback: str | None) -> PlanArtifact:
        LOGGER.info("Planner analysing specification for %s", request.function_name)
        prompt = self._build_prompt(request, stack_context, audit_feedback)
        raw = self._invoke(prompt)
        return self._parse(raw, request, stack_context)

    def _build_prompt(self, request: FunctionRequest, stack_context: str, audit_feedback: str | None) -> str:
        prompt = (
            "You are the Planner Agent in a software development pipeline. "
            "Analyse the function specification, understand the context, "
            "and produce a structured development plan with clear acceptance criteria.\n\n"
            f"Function specification:\n{request.specification}\n\n"
        )
        if stack_context:
            prompt += f"Stack guidelines to apply:\n{stack_context}\n\n"
        if audit_feedback:
            prompt += f"Auditor feedback requiring plan revision:\n{audit_feedback}\n\n"
        prompt += (
            "Respond with a single JSON object and nothing else:\n"
            '{\n'
            '  "title": "<short plan title>",\n'
            '  "context_summary": "<what was understood from the request>",\n'
            '  "stack_guidelines_applied": ["<guideline 1>", ...],\n'
            '  "specifications": "<detailed spec for the developer>",\n'
            '  "acceptance_criteria": ["<criterion 1>", ...],\n'
            '  "documentation": "<doc string and usage notes>"\n'
            '}'
        )
        return prompt

    def _parse(self, raw: str, request: FunctionRequest, stack_context: str) -> PlanArtifact:
        data = _extract_json(raw)
        if data:
            try:
                return PlanArtifact.model_validate(data)
            except (ValidationError, Exception):
                pass
        return PassthroughPlanner().plan(request, stack_context, None)

    def _invoke(self, prompt: str) -> str:
        llm = ChatOllama(model=self._model, base_url=self._base_url, temperature=0)
        response = llm.invoke(
            [
                SystemMessage(content="You are a precise planning agent. Respond only with valid JSON."),
                HumanMessage(content=prompt),
            ]
        )
        return response.content if isinstance(response.content, str) else str(response.content)


class OllamaCoder(CoderPort):
    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL) -> None:
        self._model = model
        self._base_url = base_url

    def generate(self, request: FunctionRequest, attempt: int, feedback: str | None) -> GeneratedArtifact:
        LOGGER.info("Coder round %s for %s", attempt, request.function_name)
        with ThreadPoolExecutor(max_workers=2) as executor:
            function_future = executor.submit(self._generate_function_code, request, feedback)
            tests_future = executor.submit(self._generate_test_code, request, feedback)
            function_code = function_future.result()
            test_code = tests_future.result()

        return GeneratedArtifact(
            function_name=request.function_name,
            function_code=function_code,
            test_code=test_code,
        )

    def _generate_function_code(self, request: FunctionRequest, feedback: str | None) -> str:
        prompt = (
            "You are the Coder Agent in a local software automation graph. "
            "Return only Python source code for module `subject.py`. "
            f"Implement exactly the function `{request.function_name}` described below. "
            "Do not include Markdown fences or explanations.\n\n"
            f"Function specification:\n{request.specification}\n\n"
            "Constraints:\n"
            "- Use only the Python standard library.\n"
            "- Include precise type hints.\n"
            "- Raise explicit exceptions required by the specification.\n"
            "- Do not use eval, exec, subprocess, or os.system.\n"
        )
        if feedback:
            prompt += f"\nFix the implementation using this feedback:\n{feedback}\n"
        return self._invoke(prompt)

    def _generate_test_code(self, request: FunctionRequest, feedback: str | None) -> str:
        prompt = (
            "You are the Test Author Agent in a local software automation graph. "
            "Return only Python source code for module `test_subject.py`. "
            f"Write exhaustive pytest tests for `{request.function_name}` based on the specification below. "
            "Import the function with `from subject import "
            f"{request.function_name}`. Do not include Markdown fences or explanations.\n\n"
            f"Function specification:\n{request.specification}\n\n"
            "Coverage requirements:\n"
            "- Include happy-path tests.\n"
            "- Include edge cases and invalid-input tests.\n"
            "- Prefer parametrize when it improves clarity.\n"
            "- Do not use network, file-system, or subprocess operations.\n"
        )
        if feedback:
            prompt += f"\nRevise the tests using this feedback:\n{feedback}\n"
        return self._invoke(prompt)

    def _invoke(self, prompt: str) -> str:
        llm = ChatOllama(model=self._model, base_url=self._base_url, temperature=0)
        response = llm.invoke(
            [
                SystemMessage(
                    content=(
                        "You are part of a deterministic coding pipeline. "
                        "Respond with raw Python code only."
                    )
                ),
                HumanMessage(content=prompt),
            ]
        )
        return strip_code_fences(response.content)


class OllamaContractValidator(ContractValidatorPort):
    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL) -> None:
        self._model = model
        self._base_url = base_url

    def validate_contract(self, plan: PlanArtifact, artifact: GeneratedArtifact) -> ContractReport:
        LOGGER.info("Contract validator checking %s against plan", artifact.function_name)
        criteria_str = "\n".join(f"- {c}" for c in plan.acceptance_criteria)
        prompt = (
            "You are the Contract Validator Agent. "
            "Compare the generated function code against the acceptance criteria.\n\n"
            f"Acceptance criteria:\n{criteria_str}\n\n"
            f"Generated function code:\n```python\n{artifact.function_code}\n```\n\n"
            "Respond with a single JSON object and nothing else:\n"
            '{\n'
            '  "success": true,\n'
            '  "checked_criteria": ["<criterion 1>", ...],\n'
            '  "failed_criteria": [],\n'
            '  "feedback": null\n'
            '}\n'
            "Set success=false and list failed_criteria when any criterion is unmet. "
            "Set feedback to a corrective summary when success is false."
        )
        raw = self._invoke(prompt)
        return self._parse(raw, plan)

    def _parse(self, raw: str, plan: PlanArtifact) -> ContractReport:
        data = _extract_json(raw)
        if data:
            try:
                return ContractReport.model_validate(data)
            except (ValidationError, Exception):
                pass
        return PassthroughContractValidator().validate_contract(plan, GeneratedArtifact(
            function_name="unknown", function_code="pass  # fallback", test_code="pass  # fallback"
        ))

    def _invoke(self, prompt: str) -> str:
        llm = ChatOllama(model=self._model, base_url=self._base_url, temperature=0)
        response = llm.invoke(
            [
                SystemMessage(content="You are a precise validation agent. Respond only with valid JSON."),
                HumanMessage(content=prompt),
            ]
        )
        return response.content if isinstance(response.content, str) else str(response.content)


class OllamaAuditor(AuditorPort):
    def __init__(self, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL) -> None:
        self._model = model
        self._base_url = base_url

    def audit(
        self,
        plan: PlanArtifact,
        artifact: GeneratedArtifact,
        contract: ContractReport,
        attempt: int,
    ) -> AuditReport:
        LOGGER.info("Auditor reviewing attempt %s for %s", attempt, artifact.function_name)
        failed_str = ", ".join(contract.failed_criteria) or "none"
        prompt = (
            "You are the Auditor Agent, acting as a quality manager for the development pipeline. "
            "Review the plan, generated code, and contract validation result.\n\n"
            f"Plan: {plan.title}\n"
            f"Specifications (excerpt): {plan.specifications[:400]}\n\n"
            f"Contract validation success: {contract.success}\n"
            f"Failed criteria: {failed_str}\n\n"
            f"Generated code (excerpt):\n```python\n{artifact.function_code[:800]}\n```\n\n"
            f"Correction attempt: {attempt}\n\n"
            "Check for best-practice violations and scope creep. "
            "Only request a plan rework when the specification itself is fundamentally wrong. "
            "Respond with a single JSON object and nothing else:\n"
            '{\n'
            '  "approved": true,\n'
            '  "best_practices_violations": [],\n'
            '  "scope_violations": [],\n'
            '  "requires_user_action": false,\n'
            '  "user_action_description": null,\n'
            '  "requires_plan_rework": false,\n'
            '  "feedback": null\n'
            '}'
        )
        raw = self._invoke(prompt)
        return self._parse(raw, contract)

    def _parse(self, raw: str, contract: ContractReport) -> AuditReport:
        data = _extract_json(raw)
        if data:
            try:
                return AuditReport.model_validate(data)
            except (ValidationError, Exception):
                pass
        return PassthroughAuditor().audit(
            PlanArtifact(
                title="fallback",
                context_summary="fallback",
                specifications="pass  # fallback",
                acceptance_criteria=["pass"],
                documentation="fallback",
            ),
            GeneratedArtifact(function_name="unknown", function_code="pass  # fallback", test_code="pass  # fallback"),
            contract,
            0,
        )

    def _invoke(self, prompt: str) -> str:
        llm = ChatOllama(model=self._model, base_url=self._base_url, temperature=0)
        response = llm.invoke(
            [
                SystemMessage(content="You are a precise audit agent. Respond only with valid JSON."),
                HumanMessage(content=prompt),
            ]
        )
        return response.content if isinstance(response.content, str) else str(response.content)


class CompiledGraph(Protocol):
    def invoke(self, input: AgentState, config: dict[str, Any] | None = None) -> dict[str, Any]:
        ...

    def get_state(self, config: dict[str, Any]) -> Any:
        ...

    def get_state_history(self, config: dict[str, Any]) -> Any:
        ...


def strip_code_fences(text: str) -> str:
    match = CODE_BLOCK_RE.search(text)
    return (match.group(1) if match else text).strip()


def infer_function_name(specification: str) -> str:
    match = SIGNATURE_RE.search(specification)
    if match:
        return match.group(1)
    fallback = re.sub(r"[^a-zA-Z0-9]+", "_", specification.lower()).strip("_")
    if not fallback:
        return "generated_function"
    if fallback[0].isdigit():
        fallback = f"generated_{fallback}"
    return fallback[:40]


def build_request(specification: str) -> FunctionRequest:
    return FunctionRequest(specification=specification, function_name=infer_function_name(specification))


def format_feedback(report: ValidationReport) -> str | None:
    if report.feedback:
        return report.feedback
    if report.blocked_reason:
        return report.blocked_reason
    return None


def build_services(model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL) -> PipelineServices:
    return PipelineServices(
        planner=OllamaPlanner(model=model, base_url=base_url),
        coder=OllamaCoder(model=model, base_url=base_url),
        tester=TesterAgent(),
        contract_validator=OllamaContractValidator(model=model, base_url=base_url),
        auditor=OllamaAuditor(model=model, base_url=base_url),
    )


def planner_node(state: AgentState, services: PipelineServices) -> dict[str, Any]:
    request = FunctionRequest.model_validate(state["request"])
    stack_context = load_stack_context(state.get("stack"))
    audit_feedback: str | None = None
    if state.get("audit_report"):
        audit = AuditReport.model_validate(state["audit_report"])
        audit_feedback = audit.feedback
    next_planner_attempts = state.get("planner_attempts", 0) + 1
    plan = services.planner.plan(request=request, stack_context=stack_context, audit_feedback=audit_feedback)
    LOGGER.info("Planner round %s produced plan: %s", next_planner_attempts, plan.title)
    return {
        "planner_attempts": next_planner_attempts,
        "plan_artifact": plan.model_dump(),
        "status": "planning",
        "messages": [AIMessage(content=f"Planner produced plan: {plan.title}")],
    }


def coder_node(state: AgentState, services: PipelineServices) -> dict[str, Any]:
    request = FunctionRequest.model_validate(state["request"])
    plan = PlanArtifact.model_validate(state["plan_artifact"]) if state.get("plan_artifact") else None

    if plan:
        criteria_str = "\n".join(f"- {c}" for c in plan.acceptance_criteria)
        enriched = f"{plan.specifications}\n\nAcceptance criteria:\n{criteria_str}"
        effective_request = FunctionRequest(
            specification=enriched[:SPEC_MAX_LENGTH],
            function_name=request.function_name,
        )
    else:
        effective_request = request

    previous_report = (
        ValidationReport.model_validate(state["validation_report"])
        if state.get("validation_report")
        else None
    )
    previous_contract = (
        ContractReport.model_validate(state["contract_report"])
        if state.get("contract_report")
        else None
    )

    next_attempt = state["attempt"] + 1

    feedback_parts: list[str] = []
    if previous_report:
        fb = format_feedback(previous_report)
        if fb:
            feedback_parts.append(f"Test feedback:\n{fb}")
    if previous_contract and not previous_contract.success and previous_contract.feedback:
        feedback_parts.append(f"Specification compliance feedback:\n{previous_contract.feedback}")
    feedback = "\n\n".join(feedback_parts) or None

    artifact = services.coder.generate(request=effective_request, attempt=next_attempt, feedback=feedback)
    return {
        "attempt": next_attempt,
        "artifact": artifact.model_dump(),
        "status": "drafted",
        "messages": [
            AIMessage(
                content=f"Coder round {next_attempt} produced implementation and tests for {artifact.function_name}."
            )
        ],
    }


def tester_node(state: AgentState, services: PipelineServices) -> dict[str, Any]:
    artifact = GeneratedArtifact.model_validate(state["artifact"])
    report = services.tester.validate(artifact)

    if report.blocked_reason:
        status: Literal["queued", "planning", "drafted", "retrying", "validating", "auditing", "completed", "failed"] = "failed"
    elif report.success:
        status = "drafted"
    elif state["attempt"] >= MAX_CORRECTION_ROUNDS:
        status = "failed"
    else:
        status = "retrying"

    message = "Tests passed." if report.success else (report.feedback or "Tests failed.")
    LOGGER.info("Tester round %s success=%s", state["attempt"], report.success)
    return {
        "validation_report": report.model_dump(),
        "status": status,
        "messages": [AIMessage(content=message)],
    }


def validator_node(state: AgentState, services: PipelineServices) -> dict[str, Any]:
    artifact = GeneratedArtifact.model_validate(state["artifact"])
    plan = PlanArtifact.model_validate(state["plan_artifact"]) if state.get("plan_artifact") else None

    if plan is None:
        report = ContractReport(success=True, checked_criteria=[], failed_criteria=[], feedback=None)
    else:
        report = services.contract_validator.validate_contract(plan=plan, artifact=artifact)

    message = "Contract validation passed." if report.success else (report.feedback or "Contract validation failed.")
    LOGGER.info("Contract validator success=%s for %s", report.success, artifact.function_name)
    return {
        "contract_report": report.model_dump(),
        "status": "validating",
        "messages": [AIMessage(content=message)],
    }


def auditor_node(state: AgentState, services: PipelineServices) -> dict[str, Any]:
    artifact = GeneratedArtifact.model_validate(state["artifact"])
    plan = PlanArtifact.model_validate(state["plan_artifact"]) if state.get("plan_artifact") else None
    contract = ContractReport.model_validate(state["contract_report"]) if state.get("contract_report") else None

    if plan is None or contract is None:
        audit = AuditReport(approved=True)
    else:
        audit = services.auditor.audit(plan=plan, artifact=artifact, contract=contract, attempt=state["attempt"])

    if audit.approved:
        status: Literal["queued", "planning", "drafted", "retrying", "validating", "auditing", "completed", "failed"] = "completed"
    elif audit.requires_plan_rework:
        status = "retrying"
    else:
        status = "failed"

    message = "Audit approved." if audit.approved else (audit.feedback or "Audit failed.")
    LOGGER.info("Auditor approved=%s for %s", audit.approved, artifact.function_name)
    return {
        "audit_report": audit.model_dump(),
        "status": status,
        "messages": [AIMessage(content=message)],
    }


def route_after_testing(state: AgentState) -> Literal["validator", "coder", "end"]:
    report = ValidationReport.model_validate(state["validation_report"])
    if report.blocked_reason:
        return "end"
    if report.success:
        return "validator"
    if state["attempt"] >= MAX_CORRECTION_ROUNDS:
        return "end"
    return "coder"


def route_after_validation(state: AgentState) -> Literal["auditor", "coder", "end"]:
    contract = ContractReport.model_validate(state["contract_report"])
    if contract.success:
        return "auditor"
    if state["attempt"] >= MAX_CORRECTION_ROUNDS:
        return "end"
    return "coder"


def route_after_audit(state: AgentState) -> Literal["planner", "end"]:
    audit = AuditReport.model_validate(state["audit_report"])
    if audit.approved:
        return "end"
    if audit.requires_plan_rework and state.get("planner_attempts", 0) < MAX_PLANNER_ROUNDS:
        return "planner"
    return "end"


def build_graph(services: PipelineServices | None = None) -> CompiledGraph:
    runtime_services = services or build_services()
    workflow = StateGraph(AgentState)
    workflow.add_node("planner", lambda state: planner_node(state, runtime_services))
    workflow.add_node("coder", lambda state: coder_node(state, runtime_services))
    workflow.add_node("tester", lambda state: tester_node(state, runtime_services))
    workflow.add_node("validator", lambda state: validator_node(state, runtime_services))
    workflow.add_node("auditor", lambda state: auditor_node(state, runtime_services))
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "coder")
    workflow.add_edge("coder", "tester")
    workflow.add_conditional_edges(
        "tester",
        route_after_testing,
        {"validator": "validator", "coder": "coder", "end": END},
    )
    workflow.add_conditional_edges(
        "validator",
        route_after_validation,
        {"auditor": "auditor", "coder": "coder", "end": END},
    )
    workflow.add_conditional_edges(
        "auditor",
        route_after_audit,
        {"planner": "planner", "end": END},
    )
    return workflow.compile(checkpointer=MemorySaver(), debug=False, name="function_development")


def build_runtime_config(thread_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}


def build_initial_state(request: FunctionRequest, stack: str | None = None) -> AgentState:
    return {
        "request": request.model_dump(),
        "stack": stack,
        "messages": [HumanMessage(content=request.specification)],
        "attempt": 0,
        "planner_attempts": 0,
        "plan_artifact": None,
        "artifact": None,
        "validation_report": None,
        "contract_report": None,
        "audit_report": None,
        "status": "queued",
    }


def print_summary(final_state: dict[str, Any], graph: CompiledGraph, config: dict[str, Any], show_history: bool) -> None:
    print("Final state")
    print(json.dumps(final_state, indent=2, ensure_ascii=False, default=str))

    checkpoint = graph.get_state(config)
    print("\nLatest checkpoint")
    print(f"next={checkpoint.next}")
    print(f"status={checkpoint.values.get('status')}")
    if checkpoint.values.get("plan_artifact"):
        plan = checkpoint.values["plan_artifact"]
        print(f"plan={plan.get('title', '')}")
    if checkpoint.values.get("audit_report"):
        audit = checkpoint.values["audit_report"]
        print(f"audit_approved={audit.get('approved')}")

    if not show_history:
        return

    print("\nCheckpoint history")
    for snapshot in graph.get_state_history(config):
        print(
            f"- next={snapshot.next} status={snapshot.values.get('status')} "
            f"attempt={snapshot.values.get('attempt')} "
            f"planner_attempts={snapshot.values.get('planner_attempts')}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the autonomous function development pack.")
    parser.add_argument("--spec", default=DEFAULT_SPEC, help="Function specification provided to the coder agent.")
    parser.add_argument("--spec-file", help="Optional path to a UTF-8 text file containing the function specification.")
    parser.add_argument("--stack", default=None, help="Technology stack for context (e.g. python, typescript, aws).")
    parser.add_argument("--thread-id", default=DEFAULT_THREAD_ID, help="LangGraph MemorySaver thread identifier.")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name.")
    parser.add_argument("--ollama-host", default=DEFAULT_BASE_URL, help="Ollama API base URL.")
    parser.add_argument("--log-level", default="INFO", help="Python logging level.")
    parser.add_argument("--show-history", action="store_true", help="Print LangGraph checkpoint history after execution.")
    return parser.parse_args()


def read_specification(args: argparse.Namespace) -> str:
    if not args.spec_file:
        return args.spec
    return Path(args.spec_file).read_text(encoding="utf-8")


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(levelname)s %(name)s %(message)s",
    )

    try:
        request = build_request(read_specification(args))
    except (OSError, ValidationError, ValueError) as exc:
        LOGGER.error("Invalid function specification: %s", exc)
        return 1

    graph = build_graph(build_services(model=args.model, base_url=args.ollama_host))
    config = build_runtime_config(args.thread_id)

    try:
        final_state = graph.invoke(build_initial_state(request, stack=args.stack), config=config)
    except Exception as exc:  # pragma: no cover - runtime integration safeguard
        LOGGER.exception("Pipeline execution failed: %s", exc)
        return 1

    print_summary(final_state, graph, config, show_history=args.show_history)
    report_payload = final_state.get("validation_report")
    if not report_payload:
        LOGGER.error("Pipeline finished without a validation report.")
        return 1
    report = ValidationReport.model_validate(report_payload)
    return 0 if report.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
