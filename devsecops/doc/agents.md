# Agents

El pack `devsecops` orquesta siete agentes especializados. Todos comparten `AgentState` y se comunican exclusivamente a través de él. Ningún agente escribe directamente en repositorios o entornos productivos.

---

## Orchestrator

**Rol:** Coordinador y árbitro del flujo. Decide el siguiente paso tras cada ciclo.

**Lógica de routing:**
- Si `workflow_queue` no está vacía → delega al primer agente de la cola.
- Si la cola está vacía y hay `audit_findings` y `cycle < MAX_CYCLES` → inicia nuevo ciclo.
- Si la cola está vacía y no hay más ciclos → `status = completed`.

---

## ThreatIntel Agent

**Rol:** Investigar novedades de seguridad, CVEs recientes y advisories cloud.

**Tool:** `fetch_threat_intel(context: str) → list[ThreatIntelItem]`

**Entrada del estado:** `context`

**Salida al estado:** `threat_intel: list[ThreatIntelItem]`

**Fallback determinista:** Devuelve un set curado de CVEs activos (CVE-2024-21626, OWASP Top 10 2024, advisories AWS/GH).

---

## Architect Agent

**Rol:** Traducir inteligencia de amenazas en un plan técnico priorizado.

**Tool:** `plan_architecture(threat_intel, context) → list[ArchPlanItem]`

**Entrada del estado:** `threat_intel`, `context`

**Salida al estado:** `arch_plan: list[ArchPlanItem]`

**Campos de `ArchPlanItem`:** `id`, `area`, `priority`, `description`, `proposed_change`, `rationale`

---

## Builder Agent

**Rol:** Generar propuestas IaC (Terraform, Dockerfile, K8s, OPA) basadas en el plan de arquitectura.

**Tool:** `generate_iac_proposals(arch_plan) → list[BuildProposal]`

**Entrada del estado:** `arch_plan`

**Salida al estado:** `build_proposals: list[BuildProposal]`

**Campos de `BuildProposal`:** `id`, `file_type`, `file_name`, `content`, `description`

---

## Deployment Agent

**Rol:** Crear un plan de despliegue seguro paso a paso con procedimientos de rollback.

**Tool:** `create_deployment_plan(build_proposals) → list[DeploymentStep]`

**Entrada del estado:** `build_proposals`

**Salida al estado:** `deployment_plan: list[DeploymentStep]`

**Campos de `DeploymentStep`:** `order`, `action`, `command`, `rollback`, `risk`

**Política:** Todos los pasos son propuestas. El paso 8 (producción) requiere aprobación humana explícita fuera del runtime.

---

## Auditor Agent

**Rol:** Ejecutar SAST e IaC audit continuo sobre Python, Dockerfiles y Terraform.

**Tool:** `run_audit(target_dir: str) → list[AuditFinding]`

**Entrada del estado:** `target_dir`

**Salida al estado:** `audit_findings: list[AuditFinding]`

**Campos de `AuditFinding`:** `id`, `rule_id`, `severity`, `owasp_top10`, `file_path`, `line`, `snippet`, `description`

**Reglas activas:**

| Rule ID | Tipo | Severidad | OWASP |
|---|---|---|---|
| `HARDCODED-SECRET` | Python | high | A02 |
| `SQLI-FSTRING` | Python | critical | A03 |
| `SUBPROCESS-SHELL` | Python | high | A03 |
| `RUN-AS-ROOT` | Dockerfile | high | A05 |
| `MISSING-USER` | Dockerfile | high | A05 |
| `LATEST-TAG` | Dockerfile | medium | A06 |
| `OPEN-CIDR` | Terraform | critical | A05 |
| `PUBLIC-RESOURCE` | Terraform | high | A01 |

---

## Remediator Agent

**Rol:** Proponer parches de código y configuración para cada hallazgo del Auditor.

**Tool:** `propose_remediations(findings) → list[RemediationPatch]`

**Entrada del estado:** `audit_findings`

**Salida al estado:** `patches: list[RemediationPatch]`

**Campos de `RemediationPatch`:** `finding_id`, `file_path`, `original_code`, `patched_code`, `summary`, `vector_prevented`

---

## Contrato colaborativo

- Todos los agentes leen únicamente campos de estado que les corresponden.
- Todas las salidas son listas validadas con Pydantic antes de persistirse en estado.
- El LLM nunca recibe estado completo; solo recibe el input mínimo necesario para su tool call.
- Todos los agentes tienen fallback determinista que produce output válido sin Ollama.
