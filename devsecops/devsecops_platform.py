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
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, ConfigDict, Field, ValidationError

LOGGER = logging.getLogger("agia.devsecops")
DEFAULT_MODEL: Final[str] = os.getenv("OLLAMA_MODEL", "llama3.1")
DEFAULT_BASE_URL: Final[str] = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
MAX_CYCLES: Final[int] = int(os.getenv("DEVSECOPS_MAX_CYCLES", "2"))

# ── Data Models ───────────────────────────────────────────────────────────────


class ThreatIntelItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=4, max_length=64)
    source: str = Field(min_length=2, max_length=120)
    title: str = Field(min_length=5, max_length=200)
    severity: Literal["critical", "high", "medium", "low"]
    description: str = Field(min_length=10, max_length=500)
    action_required: str = Field(min_length=5, max_length=300)


class ArchPlanItem(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=4, max_length=64)
    area: str = Field(min_length=3, max_length=100)
    priority: Literal["critical", "high", "medium", "low"]
    description: str = Field(min_length=10, max_length=500)
    proposed_change: str = Field(min_length=10, max_length=500)
    rationale: str = Field(min_length=10, max_length=500)


class BuildProposal(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=4, max_length=64)
    file_type: Literal["terraform", "dockerfile", "k8s-manifest", "policy"]
    file_name: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=10, max_length=4000)
    description: str = Field(min_length=10, max_length=300)


class DeploymentStep(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    order: int = Field(ge=1, le=100)
    action: str = Field(min_length=5, max_length=200)
    command: str = Field(min_length=3, max_length=500)
    rollback: str = Field(min_length=5, max_length=500)
    risk: Literal["low", "medium", "high"]


class AuditFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(min_length=8, max_length=64)
    rule_id: str = Field(min_length=3, max_length=80)
    severity: Literal["critical", "high", "medium", "low"]
    owasp_top10: str = Field(min_length=5, max_length=120)
    file_path: str = Field(min_length=1, max_length=500)
    line: int = Field(ge=1, le=50000)
    snippet: str = Field(min_length=1, max_length=500)
    description: str = Field(min_length=10, max_length=500)


class RemediationPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    finding_id: str = Field(min_length=8, max_length=64)
    file_path: str = Field(min_length=1, max_length=500)
    original_code: str = Field(min_length=1, max_length=1000)
    patched_code: str = Field(min_length=1, max_length=1000)
    summary: str = Field(min_length=10, max_length=500)
    vector_prevented: str = Field(min_length=10, max_length=500)


# ── Shared State ──────────────────────────────────────────────────────────────


class AgentState(TypedDict):
    target_dir: str
    context: str
    # per-agent accumulated outputs
    threat_intel: list[dict[str, Any]]
    arch_plan: list[dict[str, Any]]
    build_proposals: list[dict[str, Any]]
    deployment_plan: list[dict[str, Any]]
    audit_findings: list[dict[str, Any]]
    patches: list[dict[str, Any]]
    # workflow control
    workflow_queue: list[str]
    cycle: int
    messages: Annotated[list[BaseMessage], add_messages]
    errors: list[str]
    status: Literal["ready", "running", "completed", "error"]


# ── Tool helpers ──────────────────────────────────────────────────────────────


def _hid(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256(":".join(parts).encode()).hexdigest()[:12]
    return f"{prefix}-{digest}"


# ── Tools: Threat Intel Agent ─────────────────────────────────────────────────


@tool
def fetch_threat_intel(context: str) -> str:
    """Fetch simulated threat intelligence: recent CVEs, OWASP updates, and cloud hardening advisories."""
    items = [
        {
            "id": "CVE-2024-21626",
            "source": "NVD",
            "title": "runc container escape (Leaky Vessels)",
            "severity": "critical",
            "description": "runc <=1.1.11 allows container escape via process.cwd manipulation.",
            "action_required": "Upgrade runc to >=1.1.12 and rebuild affected images.",
        },
        {
            "id": "OWASP-A05-2024",
            "source": "OWASP Top 10",
            "title": "Security Misconfiguration in Top 5",
            "severity": "high",
            "description": "Hardcoded creds, open CIDR blocks, running as root remain the most common cloud misconfig.",
            "action_required": "Apply CIS Benchmarks and OPA/Gatekeeper admission policies.",
        },
        {
            "id": "AWS-ADV-2024-IAM",
            "source": "AWS Security Bulletin",
            "title": "Excessive IAM permissions enable privilege escalation",
            "severity": "high",
            "description": "Wildcard IAM actions on EC2/Lambda enable lateral movement.",
            "action_required": "Apply least-privilege IAM policies. Run IAM Access Analyzer weekly.",
        },
        {
            "id": "GHSA-2024-SUPPLY-CHAIN",
            "source": "GitHub Advisory DB",
            "title": "Supply chain risk via unpinned dependencies",
            "severity": "medium",
            "description": "Floating :latest tags introduce untested changes silently.",
            "action_required": "Pin all deps to SHA digests. Integrate Dependabot or Renovate.",
        },
    ]
    return json.dumps(items, ensure_ascii=False)


# ── Tools: Architect Agent ────────────────────────────────────────────────────


@tool
def plan_architecture(threat_intel: list[dict[str, Any]], context: str) -> str:
    """Translate threat intelligence into a prioritised architecture improvement plan."""
    plan = [
        {
            "id": _hid("ARCH", "container-runtime"),
            "area": "Container Runtime",
            "priority": "critical",
            "description": "Container runtime version unverified; may be vulnerable to escape.",
            "proposed_change": "Pin runc/containerd in CI. Add runtime integrity gate.",
            "rationale": "CVE-2024-21626 confirms critical blast radius of unpatched runtimes.",
        },
        {
            "id": _hid("ARCH", "iam-posture"),
            "area": "IAM / Access Control",
            "priority": "high",
            "description": "IAM roles may include wildcard actions.",
            "proposed_change": "Audit all roles with Access Analyzer; replace wildcards with scoped actions.",
            "rationale": "Lateral movement risk from overprivileged cloud identities.",
        },
        {
            "id": _hid("ARCH", "supply-chain"),
            "area": "Supply Chain",
            "priority": "high",
            "description": "Unpinned images create reproducibility and drift risk.",
            "proposed_change": "Pin Dockerfiles and Terraform module sources to SHA digests.",
            "rationale": "Supply chain compromise is amplified by mutable references.",
        },
        {
            "id": _hid("ARCH", "secrets"),
            "area": "Secrets Management",
            "priority": "high",
            "description": "Secrets may be embedded in source or env config.",
            "proposed_change": "Integrate vault-backed injection (Vault / AWS Secrets Manager). No static creds.",
            "rationale": "Hardcoded secrets are the leading cause of cloud breaches.",
        },
        {
            "id": _hid("ARCH", "zero-trust-network"),
            "area": "Network / Zero Trust",
            "priority": "medium",
            "description": "Flat network allows unrestricted lateral movement.",
            "proposed_change": "Implement default-deny NetworkPolicy. Require mTLS between services.",
            "rationale": "Zero Trust networking limits blast radius of compromised workloads.",
        },
    ]
    return json.dumps(plan, ensure_ascii=False)


# ── Tools: Builder Agent ──────────────────────────────────────────────────────


@tool
def generate_iac_proposals(arch_plan: list[dict[str, Any]]) -> str:
    """Generate IaC proposals (Terraform, Dockerfile, K8s manifests, OPA policies) based on architecture plan."""
    proposals = [
        {
            "id": _hid("BUILD", "hardened-dockerfile"),
            "file_type": "dockerfile",
            "file_name": "Dockerfile.hardened",
            "content": (
                "FROM python:3.11.9-slim@sha256:<pin-digest>\n"
                "WORKDIR /app\n"
                "COPY requirements.txt .\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n"
                "COPY . .\n"
                "RUN useradd -m appuser && chown -R appuser /app\n"
                "USER appuser\n"
                "HEALTHCHECK --interval=30s CMD curl -f http://localhost:8080/health || exit 1\n"
                "EXPOSE 8080\n"
                "CMD [\"python\", \"app.py\"]\n"
            ),
            "description": "Hardened Dockerfile: pinned digest, non-root user, healthcheck.",
        },
        {
            "id": _hid("BUILD", "iam-least-privilege"),
            "file_type": "terraform",
            "file_name": "iam_least_privilege.tf",
            "content": (
                'resource "aws_iam_policy" "least_privilege" {\n'
                '  name   = "app-least-privilege"\n'
                '  policy = jsonencode({\n'
                '    Version = "2012-10-17"\n'
                '    Statement = [{\n'
                '      Effect   = "Allow"\n'
                '      Action   = ["s3:GetObject", "s3:PutObject"]\n'
                '      Resource = "arn:aws:s3:::my-bucket/*"\n'
                '    }]\n'
                '  })\n'
                '}\n'
            ),
            "description": "IAM policy scoped to minimum required S3 actions; no wildcards.",
        },
        {
            "id": _hid("BUILD", "network-policy"),
            "file_type": "k8s-manifest",
            "file_name": "network-policy-default-deny.yaml",
            "content": (
                "apiVersion: networking.k8s.io/v1\n"
                "kind: NetworkPolicy\n"
                "metadata:\n"
                "  name: default-deny-all\n"
                "spec:\n"
                "  podSelector: {}\n"
                "  policyTypes:\n"
                "  - Ingress\n"
                "  - Egress\n"
            ),
            "description": "Default-deny Kubernetes NetworkPolicy; Zero Trust networking baseline.",
        },
        {
            "id": _hid("BUILD", "opa-policy"),
            "file_type": "policy",
            "file_name": "security_baseline.rego",
            "content": (
                "package kubernetes.admission\n\n"
                "deny[msg] {\n"
                "  input.request.object.spec.containers[_].securityContext.runAsRoot == true\n"
                '  msg := "Containers must not run as root"\n'
                "}\n\n"
                "deny[msg] {\n"
                "  not input.request.object.spec.securityContext.runAsNonRoot\n"
                '  msg := "Pods must enforce runAsNonRoot=true"\n'
                "}\n"
            ),
            "description": "OPA/Gatekeeper policy blocking root containers at admission time.",
        },
    ]
    return json.dumps(proposals, ensure_ascii=False)


# ── Tools: Deployment Agent ───────────────────────────────────────────────────


@tool
def create_deployment_plan(build_proposals: list[dict[str, Any]]) -> str:
    """Create a zero-trust step-by-step deployment plan with rollback procedures (proposal_only)."""
    steps = [
        {
            "order": 1,
            "action": "Snapshot current state",
            "command": "terraform state pull > terraform.backup.tfstate && docker tag app:prod app:rollback",
            "rollback": "terraform state push terraform.backup.tfstate",
            "risk": "low",
        },
        {
            "order": 2,
            "action": "Dry-run IaC changes",
            "command": "terraform plan -var-file=secure.tfvars -out=secure.tfplan",
            "rollback": "No changes applied at this step.",
            "risk": "low",
        },
        {
            "order": 3,
            "action": "Build and scan hardened image",
            "command": "docker build -f Dockerfile.hardened -t app:hardened . && trivy image app:hardened --exit-code 1 --severity HIGH,CRITICAL",
            "rollback": "docker rmi app:hardened",
            "risk": "low",
        },
        {
            "order": 4,
            "action": "Apply IAM least-privilege policy",
            "command": "terraform apply secure.tfplan",
            "rollback": "terraform apply rollback.tfplan (re-run plan against backup state)",
            "risk": "medium",
        },
        {
            "order": 5,
            "action": "Deploy hardened workload to staging",
            "command": "kubectl set image deployment/app app=app:hardened -n staging",
            "rollback": "kubectl rollout undo deployment/app -n staging",
            "risk": "medium",
        },
        {
            "order": 6,
            "action": "Apply network policy (default-deny) to staging",
            "command": "kubectl apply -f network-policy-default-deny.yaml -n staging",
            "rollback": "kubectl delete -f network-policy-default-deny.yaml -n staging",
            "risk": "high",
        },
        {
            "order": 7,
            "action": "Gate: run integration tests and smoke checks",
            "command": "pytest tests/integration/ && curl -f http://staging.internal/health",
            "rollback": "Block promotion to production; revert step 5.",
            "risk": "low",
        },
        {
            "order": 8,
            "action": "Promote to production after human approval",
            "command": "kubectl set image deployment/app app=app:hardened -n production",
            "rollback": "kubectl rollout undo deployment/app -n production",
            "risk": "high",
        },
    ]
    return json.dumps(steps, ensure_ascii=False)


# ── Tools: Auditor Agent ──────────────────────────────────────────────────────


@tool
def run_audit(target_dir: str) -> str:
    """Run SAST and IaC audit across Python, Dockerfile, and Terraform files in the target directory."""
    findings: list[dict[str, Any]] = []
    try:
        root = Path(target_dir)
        candidates = (
            list(root.rglob("*.py"))
            + list(root.rglob("Dockerfile*"))
            + list(root.rglob("*.tf"))
            + list(root.rglob("*.tfvars"))
        )
        for fp in candidates[:30]:
            try:
                source = fp.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            _scan_file(fp, source, findings)
    except Exception as exc:  # pragma: no cover
        return json.dumps({"error": str(exc)})
    return json.dumps(findings, ensure_ascii=False)


def _scan_file(fp: Path, source: str, out: list[dict[str, Any]]) -> None:
    name = fp.name.lower()
    suffix = fp.suffix.lower()
    is_py = suffix == ".py"
    is_docker = name == "dockerfile" or suffix == ".dockerfile"
    is_tf = suffix in {".tf", ".tfvars"}

    has_user = False
    for ln, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()

        if is_py:
            if re.search(r"(?i)(password|token|secret)_?key\s*=\s*['\"]", line):
                out.append(_finding(fp, ln, "HARDCODED-SECRET", "high",
                    "A02:2021-Cryptographic Failures", stripped[:120],
                    "Hardcoded credential in source code."))
            if re.search(r"execute\s*\(\s*f['\"]", line):
                out.append(_finding(fp, ln, "SQLI-FSTRING", "critical",
                    "A03:2021-Injection", stripped[:120],
                    "SQL injection via f-string query composition."))
            if re.search(r"subprocess\..*shell\s*=\s*True", line):
                out.append(_finding(fp, ln, "SUBPROCESS-SHELL", "high",
                    "A03:2021-Injection", stripped[:120],
                    "subprocess called with shell=True enables command injection."))

        if is_docker:
            low = stripped.lower()
            if low.startswith("user "):
                has_user = True
                if low == "user root":
                    out.append(_finding(fp, ln, "RUN-AS-ROOT", "high",
                        "A05:2021-Security Misconfiguration", stripped,
                        "Container explicitly runs as root."))
            if low.startswith("from ") and ":latest" in low:
                out.append(_finding(fp, ln, "LATEST-TAG", "medium",
                    "A06:2021-Vulnerable and Outdated Components", stripped[:120],
                    "Base image uses floating :latest tag."))

        if is_tf:
            if "0.0.0.0/0" in line:
                out.append(_finding(fp, ln, "OPEN-CIDR", "critical",
                    "A05:2021-Security Misconfiguration", stripped[:120],
                    "Unrestricted CIDR 0.0.0.0/0 exposes resource to the internet."))
            if "publicly_accessible = true" in line.lower():
                out.append(_finding(fp, ln, "PUBLIC-RESOURCE", "high",
                    "A01:2021-Broken Access Control", stripped[:120],
                    "Resource is explicitly publicly accessible."))

    if is_docker and not has_user:
        last = max(1, len(source.splitlines()))
        out.append(_finding(fp, last, "MISSING-USER", "high",
            "A05:2021-Security Misconfiguration", "<no USER directive>",
            "Dockerfile does not declare a non-root runtime user."))


def _finding(fp: Path, ln: int, rule: str, severity: str, owasp: str, snippet: str, desc: str) -> dict[str, Any]:
    return {
        "id": _hid("AUD", str(fp), str(ln), rule),
        "rule_id": rule,
        "severity": severity,
        "owasp_top10": owasp,
        "file_path": str(fp),
        "line": ln,
        "snippet": snippet,
        "description": desc,
    }


# ── Tools: Remediator Agent ───────────────────────────────────────────────────


@tool
def propose_remediations(findings: list[dict[str, Any]]) -> str:
    """Propose secure code and config patches for each audit finding (proposal_only, no direct writes)."""
    _templates: dict[str, tuple[str, str, str, str]] = {
        "HARDCODED-SECRET": (
            "SECRET_KEY = 'supersecret'",
            "SECRET_KEY = os.getenv('SECRET_KEY', '')",
            "Secret moved to runtime environment variable.",
            "Credential disclosure and lateral movement from leaked secrets.",
        ),
        "SQLI-FSTRING": (
            "cursor.execute(f'SELECT * FROM users WHERE id = {uid}')",
            "cursor.execute('SELECT * FROM users WHERE id = %s', (uid,))",
            "Parameterized query prevents SQL injection.",
            "Data exfiltration and data corruption via SQL injection.",
        ),
        "SUBPROCESS-SHELL": (
            "subprocess.run(cmd, shell=True)",
            "subprocess.run(cmd.split(), shell=False, check=True)",
            "Shell disabled; argument array isolates command from input.",
            "Arbitrary command execution via shell metacharacters.",
        ),
        "RUN-AS-ROOT": (
            "USER root",
            "RUN useradd -m appuser && chown -R appuser /app\nUSER appuser",
            "Container runtime switched to least-privilege non-root user.",
            "Host privilege escalation from compromised container process.",
        ),
        "MISSING-USER": (
            "<no USER directive>",
            "RUN useradd -m appuser && chown -R appuser /app\nUSER appuser",
            "Added explicit non-root runtime identity.",
            "Unrestricted root access within container.",
        ),
        "LATEST-TAG": (
            "FROM python:latest",
            "FROM python:3.11.9-slim@sha256:<pin-digest>",
            "Image pinned to immutable digest.",
            "Silent supply chain drift via mutable :latest tag.",
        ),
        "OPEN-CIDR": (
            'cidr_blocks = ["0.0.0.0/0"]',
            'cidr_blocks = ["10.0.0.0/24"]',
            "Unrestricted CIDR replaced with minimal trusted range.",
            "Internet-wide unauthorized access to cloud infrastructure.",
        ),
        "PUBLIC-RESOURCE": (
            "publicly_accessible = true",
            "publicly_accessible = false",
            "Public exposure disabled; private network controls enforced.",
            "Unauthenticated direct internet access to cloud resources.",
        ),
    }
    patches = []
    for finding in findings:
        rule = finding.get("rule_id", "")
        tmpl = _templates.get(rule)
        if tmpl:
            orig, patched, summary, vector = tmpl
        else:
            orig = finding.get("snippet", "# unknown")
            patched = "# TODO: apply secure baseline for this rule"
            summary = "Generic remediation placeholder; no specific template configured."
            vector = "Potential exploit path associated with the detected weakness."
        patches.append({
            "finding_id": finding.get("id", ""),
            "file_path": finding.get("file_path", ""),
            "original_code": orig,
            "patched_code": patched,
            "summary": summary,
            "vector_prevented": vector,
        })
    return json.dumps(patches, ensure_ascii=False)


# ── Agent Infrastructure ──────────────────────────────────────────────────────


def _make_llm(model: str, base_url: str) -> ChatOllama | None:
    try:
        return ChatOllama(model=model, base_url=base_url, temperature=0)
    except Exception as exc:
        LOGGER.warning("Ollama unavailable (%s). Deterministic mode active.", exc)
        return None


def _build_agent_input(agent_name: str, state: AgentState) -> dict[str, Any]:
    return {
        "threat_intel": {"context": state.get("context", ""), "cycle": state.get("cycle", 1)},
        "architect": {"threat_intel": state.get("threat_intel", []), "context": state.get("context", "")},
        "builder": {"arch_plan": state.get("arch_plan", [])},
        "deployment": {"build_proposals": state.get("build_proposals", [])},
        "auditor": {"target_dir": state.get("target_dir", ".")},
        "remediator": {"findings": state.get("audit_findings", [])},
    }.get(agent_name, {})


def _write_agent_output(agent_name: str, result: Any) -> dict[str, Any]:
    if not isinstance(result, list):
        result = []
    return {
        "threat_intel": {"threat_intel": result},
        "architect": {"arch_plan": result},
        "builder": {"build_proposals": result},
        "deployment": {"deployment_plan": result},
        "auditor": {"audit_findings": result},
        "remediator": {"patches": result},
    }.get(agent_name, {})


def _deterministic_result(agent_name: str, state: AgentState) -> Any:
    dispatch = {
        "threat_intel": lambda: json.loads(fetch_threat_intel.invoke({"context": state.get("context", "")})),
        "architect": lambda: json.loads(plan_architecture.invoke({"threat_intel": state.get("threat_intel", []), "context": state.get("context", "")})),
        "builder": lambda: json.loads(generate_iac_proposals.invoke({"arch_plan": state.get("arch_plan", [])})),
        "deployment": lambda: json.loads(create_deployment_plan.invoke({"build_proposals": state.get("build_proposals", [])})),
        "auditor": lambda: json.loads(run_audit.invoke({"target_dir": state.get("target_dir", ".")})) if not isinstance(json.loads(run_audit.invoke({"target_dir": state.get("target_dir", ".")})), dict) else [],
        "remediator": lambda: json.loads(propose_remediations.invoke({"findings": state.get("audit_findings", [])})),
    }
    try:
        fn = dispatch.get(agent_name)
        return fn() if fn else []
    except Exception as exc:
        LOGGER.warning("Deterministic fallback for %s failed: %s", agent_name, exc)
        return []


_TOOL_REGISTRY: dict[str, list] = {
    "threat_intel": [fetch_threat_intel],
    "architect": [plan_architecture],
    "builder": [generate_iac_proposals],
    "deployment": [create_deployment_plan],
    "auditor": [run_audit],
    "remediator": [propose_remediations],
}

_SYSTEM_PROMPTS: dict[str, str] = {
    "threat_intel": (
        "Eres el Agente de Inteligencia de Amenazas. Tu rol es investigar novedades de seguridad, "
        "CVEs recientes y advisories cloud. Usa fetch_threat_intel con el contexto dado y devuelve la lista de items."
    ),
    "architect": (
        "Eres el Agente Arquitecto DevSecOps. Traduce la inteligencia de amenazas en un plan técnico priorizado "
        "usando plan_architecture. No inventes vulnerabilidades; prioriza hallazgos del Agente de Amenazas."
    ),
    "builder": (
        "Eres el Agente Constructor de Infraestructura. Genera propuestas IaC seguras (Terraform, Dockerfile, "
        "K8s, OPA) usando generate_iac_proposals basándote en el plan de arquitectura."
    ),
    "deployment": (
        "Eres el Agente de Despliegue. Crea un plan de despliegue seguro paso a paso con rollback. "
        "Usa create_deployment_plan. Modo estricto: proposal_only, nunca ejecutes cambios directamente."
    ),
    "auditor": (
        "Eres el Agente Auditor. Ejecuta análisis SAST e IaC sobre el directorio objetivo con run_audit. "
        "Identifica vulnerabilidades OWASP Top 10 en Python, Dockerfiles y Terraform."
    ),
    "remediator": (
        "Eres el Agente Remediador. Para cada hallazgo del auditor, propone un parche de código seguro "
        "usando propose_remediations. Modo: proposal_only. No escribas archivos directamente."
    ),
}


def _make_agent_node(agent_name: str, llm: ChatOllama | None):
    agent_tools = _TOOL_REGISTRY[agent_name]
    tool_map = {t.name: t for t in agent_tools}
    bound_llm = llm.bind_tools(agent_tools) if llm else None
    system_prompt = _SYSTEM_PROMPTS[agent_name]

    def node(state: AgentState) -> dict[str, Any]:
        queue = list(state.get("workflow_queue", []))
        if queue and queue[0] == agent_name:
            queue.pop(0)

        errors = list(state.get("errors", []))
        new_messages: list[BaseMessage] = []
        result: Any = None

        if bound_llm is not None:
            try:
                human = HumanMessage(content=json.dumps(_build_agent_input(agent_name, state), ensure_ascii=False))
                response = bound_llm.invoke([SystemMessage(content=system_prompt), human])
                new_messages.extend([human, response])
                if isinstance(response, AIMessage) and response.tool_calls:
                    call = response.tool_calls[0]
                    tool_obj = tool_map.get(call["name"])
                    if tool_obj:
                        raw = tool_obj.invoke(call.get("args", {}))
                        new_messages.append(ToolMessage(content=raw, tool_call_id=call["id"], name=call["name"]))
                        data = json.loads(raw)
                        result = data if isinstance(data, list) else None
                    else:
                        errors.append(f"{agent_name}: tool {call['name']!r} not in registry. Using fallback.")
                else:
                    errors.append(f"{agent_name}: no tool call returned. Using deterministic fallback.")
            except Exception as exc:
                errors.append(f"{agent_name}: LLM error – {exc}. Using deterministic fallback.")

        if result is None:
            result = _deterministic_result(agent_name, state)

        partial: dict[str, Any] = {"workflow_queue": queue, "errors": errors, "messages": new_messages}
        partial.update(_write_agent_output(agent_name, result))
        return partial

    node.__name__ = agent_name
    return node


# ── Orchestrator ──────────────────────────────────────────────────────────────


def orchestrator_node(state: AgentState) -> dict[str, Any]:
    """Coordinate workflow: check queue, trigger re-audit cycle if needed, or signal completion."""
    queue = list(state.get("workflow_queue", []))
    cycle = state.get("cycle", 1)

    if queue:
        return {"status": "running"}

    # Queue exhausted – decide next move
    has_findings = bool(state.get("audit_findings"))
    if has_findings and cycle < MAX_CYCLES:
        new_queue = ["threat_intel", "architect", "builder", "deployment", "auditor", "remediator"]
        return {"workflow_queue": new_queue, "cycle": cycle + 1, "status": "running"}

    return {"status": "completed"}


def _route(state: AgentState) -> str:
    if state.get("status") == "completed":
        return END
    queue = state.get("workflow_queue", [])
    return queue[0] if queue else END


# ── Graph assembly ────────────────────────────────────────────────────────────


def build_graph(model: str = DEFAULT_MODEL, base_url: str = DEFAULT_BASE_URL):
    llm = _make_llm(model, base_url)
    g = StateGraph(AgentState)

    g.add_node("orchestrator", orchestrator_node)
    for name in _TOOL_REGISTRY:
        g.add_node(name, _make_agent_node(name, llm))
        g.add_edge(name, "orchestrator")

    g.add_edge(START, "orchestrator")
    g.add_conditional_edges("orchestrator", _route)

    return g.compile(checkpointer=MemorySaver())


# ── Public API ────────────────────────────────────────────────────────────────


def run_platform(
    target_dir: str,
    context: str = "",
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
) -> dict[str, Any]:
    app = build_graph(model=model, base_url=base_url)
    ctx = context or f"DevSecOps platform run on {target_dir}"
    initial: AgentState = {
        "target_dir": target_dir,
        "context": ctx,
        "threat_intel": [],
        "arch_plan": [],
        "build_proposals": [],
        "deployment_plan": [],
        "audit_findings": [],
        "patches": [],
        "workflow_queue": ["threat_intel", "architect", "builder", "deployment", "auditor", "remediator"],
        "cycle": 1,
        "messages": [],
        "errors": [],
        "status": "ready",
    }
    result = app.invoke(initial, config={"configurable": {"thread_id": f"dso-{Path(target_dir).name}"}})
    return {
        "target_dir": target_dir,
        "status": result.get("status", "error"),
        "cycles_completed": result.get("cycle", 1),
        "threat_intel_count": len(result.get("threat_intel", [])),
        "arch_plan_count": len(result.get("arch_plan", [])),
        "build_proposals_count": len(result.get("build_proposals", [])),
        "deployment_steps_count": len(result.get("deployment_plan", [])),
        "audit_findings_count": len(result.get("audit_findings", [])),
        "patches_count": len(result.get("patches", [])),
        "errors": result.get("errors", []),
        "full_report": {
            "zero_trust": True,
            "mode": "proposal_only",
            "threat_intel": result.get("threat_intel", []),
            "arch_plan": result.get("arch_plan", []),
            "build_proposals": result.get("build_proposals", []),
            "deployment_plan": result.get("deployment_plan", []),
            "audit_findings": result.get("audit_findings", []),
            "patches": result.get("patches", []),
        },
    }


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Multi-agent DevSecOps platform: research, plan, build, deploy, audit, remediate."
    )
    parser.add_argument("target", nargs="?", default=".", help="Directory to audit/platform-run (default: .)")
    parser.add_argument("--context", default="", help="Optional free-text context for the platform run")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Ollama model name")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Ollama base URL")
    parser.add_argument("--show-report", action="store_true", help="Print full JSON report after summary")
    parser.add_argument("--log-level", default=os.getenv("LOG_LEVEL", "INFO"), help="Logging level")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO))
    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        print(json.dumps({"error": f"Target not found: {target}"}, ensure_ascii=False, indent=2))
        return 1

    result = run_platform(
        target_dir=str(target),
        context=args.context,
        model=args.model,
        base_url=args.base_url,
    )
    summary = {k: v for k, v in result.items() if k != "full_report"}
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    if args.show_report:
        print("\n# Full DevSecOps Report (Zero Trust / proposal_only)")
        print(json.dumps(result["full_report"], ensure_ascii=False, indent=2))

    return 0 if result.get("status") == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
