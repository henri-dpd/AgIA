from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import re
from pathlib import Path
from typing import Annotated, Any, Final, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool, tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field, ValidationError

LOGGER = logging.getLogger("agia.devsecops_audit")
DEFAULT_MODEL: Final[str] = os.getenv("OLLAMA_MODEL", "llama3.1")
DEFAULT_BASE_URL: Final[str] = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")


class VulnerabilityFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=8, max_length=64)
    rule_id: str = Field(min_length=3, max_length=80)
    tool: Literal["bandit-sim", "semgrep-sim", "iac-sim"]
    severity: Literal["critical", "high", "medium", "low"]
    owasp_top10: str = Field(min_length=5, max_length=120)
    file_path: str = Field(min_length=1, max_length=500)
    line: int = Field(ge=1, le=50000)
    snippet: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=10, max_length=500)
    recommendation: str = Field(min_length=10, max_length=500)


class SecurePatch(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    vulnerability_id: str = Field(min_length=8, max_length=64)
    file_path: str = Field(min_length=1, max_length=500)
    original_code: str = Field(min_length=1, max_length=1000)
    patched_code: str = Field(min_length=1, max_length=1000)
    mitigation_summary: str = Field(min_length=10, max_length=500)
    attack_vector_prevented: str = Field(min_length=10, max_length=500)


class MitigationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zero_trust: bool = True
    mode: Literal["proposal_only"] = "proposal_only"
    target_file: str
    vulnerabilities: list[VulnerabilityFinding]
    secure_patches: list[SecurePatch]
    risk_summary: str


class AgentState(TypedDict):
    target_file: str
    source_code: str
    file_type: Literal["python", "dockerfile", "terraform", "unknown"]
    vulnerabilities: list[dict[str, Any]]
    secure_patches: list[dict[str, Any]]
    payload: dict[str, Any] | None
    messages: Annotated[list[BaseMessage], add_messages]
    errors: list[str]
    status: Literal["ready", "analyzed", "mitigated", "completed", "error"]


def _hash_finding(file_path: str, line: int, rule_id: str) -> str:
    seed = f"{file_path}:{line}:{rule_id}".encode("utf-8")
    return hashlib.sha256(seed).hexdigest()[:16]


def _detect_file_type(target_file: str) -> Literal["python", "dockerfile", "terraform", "unknown"]:
    path = Path(target_file)
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix == ".py":
        return "python"
    if name == "dockerfile" or suffix == ".dockerfile":
        return "dockerfile"
    if suffix in {".tf", ".tfvars"}:
        return "terraform"
    return "unknown"


@tool
def scan_python_source(file_path: str, source: str) -> str:
    """Simulate SAST checks for insecure Python patterns (Bandit/Semgrep style)."""

    findings: list[dict[str, Any]] = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        if re.search(r"(?i)(password|token|secret)_?key\s*=\s*['\"]", line):
            findings.append(
                {
                    "id": _hash_finding(file_path, line_no, "PY-HARDCODED-SECRET"),
                    "rule_id": "PY-HARDCODED-SECRET",
                    "tool": "bandit-sim",
                    "severity": "high",
                    "owasp_top10": "A02:2021-Cryptographic Failures",
                    "file_path": file_path,
                    "line": line_no,
                    "snippet": line.strip(),
                    "description": "Potential hardcoded credential detected.",
                    "recommendation": "Move secrets to environment variables or a vault-backed secret manager.",
                }
            )
        if re.search(r"execute\s*\(\s*f['\"]", line):
            findings.append(
                {
                    "id": _hash_finding(file_path, line_no, "PY-SQLI-FSTRING"),
                    "rule_id": "PY-SQLI-FSTRING",
                    "tool": "semgrep-sim",
                    "severity": "critical",
                    "owasp_top10": "A03:2021-Injection",
                    "file_path": file_path,
                    "line": line_no,
                    "snippet": line.strip(),
                    "description": "Potential SQL injection via f-string query composition.",
                    "recommendation": "Use parameterized queries and separate SQL from user-supplied values.",
                }
            )
        if re.search(r"subprocess\..*shell\s*=\s*True", line):
            findings.append(
                {
                    "id": _hash_finding(file_path, line_no, "PY-SUBPROCESS-SHELL"),
                    "rule_id": "PY-SUBPROCESS-SHELL",
                    "tool": "bandit-sim",
                    "severity": "high",
                    "owasp_top10": "A03:2021-Injection",
                    "file_path": file_path,
                    "line": line_no,
                    "snippet": line.strip(),
                    "description": "Shell invocation with shell=True increases command injection risk.",
                    "recommendation": "Invoke subprocess with argument arrays and shell=False.",
                }
            )
    return json.dumps(findings, ensure_ascii=False)


@tool
def scan_dockerfile(file_path: str, source: str) -> str:
    """Simulate static checks for insecure Dockerfile patterns."""

    findings: list[dict[str, Any]] = []
    has_user = False
    for line_no, line in enumerate(source.splitlines(), start=1):
        lowered = line.strip().lower()
        if lowered.startswith("user "):
            has_user = True
            if lowered == "user root":
                findings.append(
                    {
                        "id": _hash_finding(file_path, line_no, "DOCKER-RUN-AS-ROOT"),
                        "rule_id": "DOCKER-RUN-AS-ROOT",
                        "tool": "iac-sim",
                        "severity": "high",
                        "owasp_top10": "A05:2021-Security Misconfiguration",
                        "file_path": file_path,
                        "line": line_no,
                        "snippet": line.strip(),
                        "description": "Container runs as root user.",
                        "recommendation": "Create and switch to a non-root user before runtime instructions.",
                    }
                )
        if lowered.startswith("from ") and ":latest" in lowered:
            findings.append(
                {
                    "id": _hash_finding(file_path, line_no, "DOCKER-LATEST-TAG"),
                    "rule_id": "DOCKER-LATEST-TAG",
                    "tool": "iac-sim",
                    "severity": "medium",
                    "owasp_top10": "A06:2021-Vulnerable and Outdated Components",
                    "file_path": file_path,
                    "line": line_no,
                    "snippet": line.strip(),
                    "description": "Base image uses floating latest tag.",
                    "recommendation": "Pin to a specific digest or immutable version tag.",
                }
            )

    if not has_user:
        findings.append(
            {
                "id": _hash_finding(file_path, max(1, len(source.splitlines())), "DOCKER-MISSING-USER"),
                "rule_id": "DOCKER-MISSING-USER",
                "tool": "iac-sim",
                "severity": "high",
                "owasp_top10": "A05:2021-Security Misconfiguration",
                "file_path": file_path,
                "line": max(1, len(source.splitlines())),
                "snippet": "<no USER directive>",
                "description": "Dockerfile does not declare a non-root runtime user.",
                "recommendation": "Add user creation and USER directive in final stage.",
            }
        )
    return json.dumps(findings, ensure_ascii=False)


@tool
def scan_terraform_source(file_path: str, source: str) -> str:
    """Simulate IaC checks for insecure Terraform patterns."""

    findings: list[dict[str, Any]] = []
    for line_no, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip().lower()
        if "0.0.0.0/0" in stripped:
            findings.append(
                {
                    "id": _hash_finding(file_path, line_no, "TF-OPEN-CIDR"),
                    "rule_id": "TF-OPEN-CIDR",
                    "tool": "iac-sim",
                    "severity": "critical",
                    "owasp_top10": "A05:2021-Security Misconfiguration",
                    "file_path": file_path,
                    "line": line_no,
                    "snippet": line.strip(),
                    "description": "Terraform rule allows unrestricted network ingress/egress.",
                    "recommendation": "Restrict CIDR blocks to required network ranges.",
                }
            )
        if "publicly_accessible = true" in stripped:
            findings.append(
                {
                    "id": _hash_finding(file_path, line_no, "TF-PUBLIC-RESOURCE"),
                    "rule_id": "TF-PUBLIC-RESOURCE",
                    "tool": "iac-sim",
                    "severity": "high",
                    "owasp_top10": "A01:2021-Broken Access Control",
                    "file_path": file_path,
                    "line": line_no,
                    "snippet": line.strip(),
                    "description": "Managed resource is explicitly publicly accessible.",
                    "recommendation": "Disable public exposure and apply private network controls.",
                }
            )
    return json.dumps(findings, ensure_ascii=False)


@tool
def propose_secure_patch(vulnerability: dict[str, Any]) -> str:
    """Build a secure patch proposal in JSON without touching files."""

    finding = VulnerabilityFinding.model_validate(vulnerability)
    patches: dict[str, tuple[str, str, str, str]] = {
        "PY-HARDCODED-SECRET": (
            finding.snippet,
            "password = os.getenv('APP_PASSWORD', '')",
            "Hardcoded secret replaced with runtime secret retrieval.",
            "Credential disclosure and lateral movement from leaked secrets.",
        ),
        "PY-SQLI-FSTRING": (
            finding.snippet,
            "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
            "Unsafe SQL concatenation replaced by parameterized query.",
            "SQL injection and data exfiltration via crafted user input.",
        ),
        "PY-SUBPROCESS-SHELL": (
            finding.snippet,
            "subprocess.run(['ls', '-la'], shell=False, check=True)",
            "Shell execution disabled and command arguments isolated.",
            "Command injection through shell metacharacters.",
        ),
        "DOCKER-RUN-AS-ROOT": (
            finding.snippet,
            "RUN useradd -m appuser && chown -R appuser /app\nUSER appuser",
            "Container runtime switched to least-privilege user.",
            "Privilege escalation from compromised container process.",
        ),
        "DOCKER-MISSING-USER": (
            finding.snippet,
            "RUN useradd -m appuser && chown -R appuser /app\nUSER appuser",
            "Added explicit non-root runtime identity.",
            "Default root runtime abuse for host-impacting actions.",
        ),
        "DOCKER-LATEST-TAG": (
            finding.snippet,
            "FROM python:3.11.9-slim@sha256:<digest>",
            "Base image pinned to immutable version and digest.",
            "Unexpected vulnerable image drift from mutable latest tag.",
        ),
        "TF-OPEN-CIDR": (
            finding.snippet,
            'cidr_blocks = ["10.0.0.0/24"]',
            "Unrestricted CIDR replaced with minimal trusted range.",
            "Internet-wide attack surface and unauthorized access.",
        ),
        "TF-PUBLIC-RESOURCE": (
            finding.snippet,
            "publicly_accessible = false",
            "Public resource exposure disabled.",
            "Unauthorized direct internet access to cloud resources.",
        ),
    }

    original_code, patched_code, mitigation_summary, attack_vector_prevented = patches.get(
        finding.rule_id,
        (
            finding.snippet,
            "# TODO: apply secure coding baseline for this rule",
            "Generated generic mitigation because no rule-specific template was configured.",
            "Potential exploit path associated with the detected weakness.",
        ),
    )
    patch = SecurePatch(
        vulnerability_id=finding.id,
        file_path=finding.file_path,
        original_code=original_code,
        patched_code=patched_code,
        mitigation_summary=mitigation_summary,
        attack_vector_prevented=attack_vector_prevented,
    )
    return patch.model_dump_json(ensure_ascii=False)


class DevSecOpsAnalyzer:
    def __init__(self, llm: ChatOllama | None) -> None:
        self._llm = llm.bind_tools([scan_python_source, scan_dockerfile, scan_terraform_source]) if llm else None

    def analyze(self, target_file: str, source: str, file_type: str) -> tuple[list[dict[str, Any]], list[BaseMessage], list[str]]:
        errors: list[str] = []
        messages: list[BaseMessage] = []

        if self._llm is not None and file_type in {"python", "dockerfile", "terraform"}:
            prompt = (
                "Eres el Agente Analizador SAST/IaC. Usa exactamente una herramienta de escaneo acorde al tipo de archivo "
                "y devuelve hallazgos estructurados."
            )
            human = HumanMessage(
                content=json.dumps(
                    {
                        "target_file": target_file,
                        "file_type": file_type,
                        "source_preview": source[:3000],
                        "required_output": "call_tool",
                    },
                    ensure_ascii=False,
                )
            )
            response = self._llm.invoke([SystemMessage(content=prompt), human])
            messages.extend([human, response])
            if isinstance(response, AIMessage) and response.tool_calls:
                tool_map: dict[str, BaseTool] = {
                    scan_python_source.name: scan_python_source,
                    scan_dockerfile.name: scan_dockerfile,
                    scan_terraform_source.name: scan_terraform_source,
                }
                for call in response.tool_calls:
                    tool_name = call.get("name", "")
                    args = call.get("args", {})
                    tool_obj = tool_map.get(tool_name)
                    if tool_obj is None:
                        errors.append(f"Tool not permitted: {tool_name}")
                        continue
                    if "file_path" not in args:
                        args["file_path"] = target_file
                    if "source" not in args:
                        args["source"] = source
                    try:
                        raw_findings = tool_obj.invoke(args)
                        tool_message = ToolMessage(
                            content=raw_findings,
                            tool_call_id=call["id"],
                            name=tool_name,
                        )
                        messages.append(tool_message)
                        decoded = json.loads(raw_findings)
                        validated = [VulnerabilityFinding.model_validate(item).model_dump() for item in decoded]
                        return validated, messages, errors
                    except (ValidationError, json.JSONDecodeError, KeyError, ValueError) as exc:
                        errors.append(f"Analyzer tool execution failed: {exc}")
            else:
                errors.append("Analyzer LLM did not return a valid tool call. Falling back to deterministic scan.")

        try:
            if file_type == "python":
                raw = scan_python_source.invoke({"file_path": target_file, "source": source})
            elif file_type == "dockerfile":
                raw = scan_dockerfile.invoke({"file_path": target_file, "source": source})
            elif file_type == "terraform":
                raw = scan_terraform_source.invoke({"file_path": target_file, "source": source})
            else:
                raw = "[]"
            decoded = json.loads(raw)
            validated = [VulnerabilityFinding.model_validate(item).model_dump() for item in decoded]
            return validated, messages, errors
        except (ValidationError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"Deterministic analysis failed: {exc}")
            return [], messages, errors


class DevSecOpsMitigator:
    def __init__(self, llm: ChatOllama | None) -> None:
        self._llm = llm.bind_tools([propose_secure_patch]) if llm else None

    def remediate(self, vulnerabilities: list[dict[str, Any]], target_file: str) -> tuple[list[dict[str, Any]], dict[str, Any], list[BaseMessage], list[str]]:
        messages: list[BaseMessage] = []
        errors: list[str] = []
        patches: list[dict[str, Any]] = []

        if self._llm is not None and vulnerabilities:
            system = SystemMessage(
                content=(
                    "Eres el Agente Mitigador. Debes usar la herramienta propose_secure_patch para cada vulnerabilidad "
                    "y no debes proponer cambios directos en producción."
                )
            )
            for vuln in vulnerabilities:
                human = HumanMessage(content=json.dumps({"vulnerability": vuln}, ensure_ascii=False))
                response = self._llm.invoke([system, human])
                messages.extend([human, response])
                if isinstance(response, AIMessage) and response.tool_calls:
                    call = response.tool_calls[0]
                    try:
                        raw_patch = propose_secure_patch.invoke({"vulnerability": call.get("args", {}).get("vulnerability", vuln)})
                        tool_message = ToolMessage(content=raw_patch, tool_call_id=call["id"], name=propose_secure_patch.name)
                        messages.append(tool_message)
                        patches.append(SecurePatch.model_validate_json(raw_patch).model_dump())
                        continue
                    except (ValidationError, KeyError, ValueError) as exc:
                        errors.append(f"Mitigator tool call failed: {exc}")
                errors.append("Mitigator LLM did not produce a valid tool call. Using deterministic fallback patch.")

        if not patches:
            for vuln in vulnerabilities:
                raw_patch = propose_secure_patch.invoke({"vulnerability": vuln})
                patches.append(SecurePatch.model_validate_json(raw_patch).model_dump())

        risk_summary = (
            "No se detectaron vulnerabilidades críticas para mitigar."
            if not vulnerabilities
            else (
                f"Se mitigaron {len(vulnerabilities)} hallazgos con propuestas seguras en modo Zero Trust "
                "(solo payload JSON, sin sobreescritura en producción)."
            )
        )
        payload = MitigationPayload(
            target_file=target_file,
            vulnerabilities=[VulnerabilityFinding.model_validate(item) for item in vulnerabilities],
            secure_patches=[SecurePatch.model_validate(item) for item in patches],
            risk_summary=risk_summary,
        ).model_dump()
        return patches, payload, messages, errors


def _build_graph(analyzer: DevSecOpsAnalyzer, mitigator: DevSecOpsMitigator):
    graph = StateGraph(AgentState)

    def analyze_node(state: AgentState) -> dict[str, Any]:
        findings, messages, errors = analyzer.analyze(
            target_file=state["target_file"],
            source=state["source_code"],
            file_type=state["file_type"],
        )
        return {
            "vulnerabilities": findings,
            "messages": messages,
            "errors": [*state["errors"], *errors],
            "status": "analyzed",
        }

    def mitigate_node(state: AgentState) -> dict[str, Any]:
        patches, payload, messages, errors = mitigator.remediate(
            vulnerabilities=state["vulnerabilities"],
            target_file=state["target_file"],
        )
        status = "completed" if not errors else "mitigated"
        return {
            "secure_patches": patches,
            "payload": payload,
            "messages": messages,
            "errors": [*state["errors"], *errors],
            "status": status,
        }

    graph.add_node("analyzer", analyze_node)
    graph.add_node("mitigator", mitigate_node)
    graph.add_edge(START, "analyzer")
    graph.add_edge("analyzer", "mitigator")
    graph.add_edge("mitigator", END)

    return graph.compile(checkpointer=MemorySaver())


def run_audit(target_file: Path, model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    source = target_file.read_text(encoding="utf-8")
    file_type = _detect_file_type(str(target_file))
    llm: ChatOllama | None
    try:
        llm = ChatOllama(model=model, base_url=base_url, temperature=0)
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Ollama unavailable, using deterministic mode: %s", exc)
        llm = None

    analyzer = DevSecOpsAnalyzer(llm=llm)
    mitigator = DevSecOpsMitigator(llm=llm)
    app = _build_graph(analyzer=analyzer, mitigator=mitigator)

    initial_state: AgentState = {
        "target_file": str(target_file),
        "source_code": source,
        "file_type": file_type,
        "vulnerabilities": [],
        "secure_patches": [],
        "payload": None,
        "messages": [],
        "errors": [],
        "status": "ready",
    }
    result = app.invoke(initial_state, config={"configurable": {"thread_id": f"audit-{target_file.name}"}})
    payload = result.get("payload") or {}
    return {
        "target_file": str(target_file),
        "file_type": file_type,
        "status": result.get("status", "error"),
        "vulnerability_count": len(result.get("vulnerabilities", [])),
        "patch_count": len(result.get("secure_patches", [])),
        "errors": result.get("errors", []),
        "mitigation_payload": payload,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Multi-agent DevSecOps auditor (SAST/IaC) with LangGraph + Ollama.")
    parser.add_argument("target", help="Path to a Python file, Dockerfile, or Terraform file")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Ollama base URL")
    parser.add_argument("--show-history", action="store_true", help="Print graph messages emitted by agents")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"), help="Logging level")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))

    target = Path(args.target).expanduser().resolve()
    if not target.exists() or not target.is_file():
        print(json.dumps({"error": f"Target file not found: {target}"}, ensure_ascii=False, indent=2))
        return 1

    result = run_audit(target_file=target, model=args.model, base_url=args.base_url)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.show_history and result.get("mitigation_payload"):
        print("\n# Zero Trust payload preview")
        print(json.dumps(result["mitigation_payload"], ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
