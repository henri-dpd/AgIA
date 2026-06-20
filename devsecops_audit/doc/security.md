# Security

## Modelo Zero Trust aplicado

- **Sin confianza implícita en el LLM:** toda salida pasa por validación Pydantic.
- **Sin escritura directa:** el sistema solo produce `MitigationPayload` JSON (`proposal_only`).
- **Mínimo privilegio:** las herramientas de análisis y remediación están cerradas por registro explícito.
- **Auditoría completa:** `messages` y `errors` quedan en el estado para trazabilidad.

## Justificación criptográfica y de integridad

- Cada hallazgo usa un identificador derivado de `sha256(file_path:line:rule_id)`.
- El identificador estable permite correlacionar hallazgos y parches sin exponer secretos.
- La derivación hash favorece integridad de cadena de evidencia durante revisiones.

## Controles frente a OWASP Top 10

El analizador prioriza patrones ligados a:

- `A02:2021-Cryptographic Failures` (secretos en duro).
- `A03:2021-Injection` (SQL/command injection).
- `A05:2021-Security Misconfiguration` (Docker/Terraform inseguros).
- `A06:2021-Vulnerable and Outdated Components` (tags mutables).

## Restricciones operativas

- El pack está diseñado para **pre-despliegue** como control de puerta.
- El payload de salida debe ser revisado por humanos o pipeline con aprobación.
- No se permite bypass de la política `proposal_only` en este runtime.
