# Agents

## Agente Analizador (`analyzer`)

**Rol:** Triage SAST/IaC sobre archivos fuente crudos (`.py`, `Dockerfile`, `.tf`).

**Entrada principal (`AgentState`):**

- `target_file`: ruta absoluta del archivo auditado.
- `source_code`: contenido textual del archivo.
- `file_type`: `python | dockerfile | terraform | unknown`.
- `errors`: historial de errores no fatales.

**Salida acumulada:**

- `vulnerabilities`: lista tipada de `VulnerabilityFinding`.
- `status`: cambia a `analyzed`.
- `messages`: mensajes del ciclo de tool-calling.

**Hallazgo (`VulnerabilityFinding`):**

- `id`, `rule_id`, `tool`, `severity`, `owasp_top10`
- `file_path`, `line`, `snippet`
- `description`, `recommendation`

## Agente Mitigador (`mitigator`)

**Rol:** Consumir hallazgos y proponer parches seguros sin modificar archivos en disco.

**Entrada principal:**

- `vulnerabilities` producidas por `analyzer`.

**Salida acumulada:**

- `secure_patches`: lista tipada de `SecurePatch`.
- `payload`: `MitigationPayload` en formato JSON (`proposal_only`).
- `status`: `mitigated` o `completed`.

**Parche (`SecurePatch`):**

- `vulnerability_id`, `file_path`
- `original_code`, `patched_code`
- `mitigation_summary`, `attack_vector_prevented`

## Contrato Zero Trust

- Los agentes no ejecutan escritura directa sobre repositorios o entornos productivos.
- Toda salida de remediación se entrega como payload estructurado y auditable.
- El payload conserva trazabilidad de hallazgo → parche propuesto.
