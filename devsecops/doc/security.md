# Security

## Política Zero Trust aplicada

El pack aplica los siguientes principios Zero Trust de extremo a extremo:

1. **Nunca confiar en el LLM por defecto.** Toda salida del modelo pasa por validación Pydantic antes de persistirse en estado.
2. **Sin escritura directa.** El sistema solo produce `MitigationPayload` y propuestas JSON (`mode: proposal_only`). Ningún agente escribe archivos en disco ni ejecuta comandos de infraestructura.
3. **Mínimo privilegio de información.** Cada LLM recibe únicamente el subconjunto de estado que necesita para su rol; nunca el estado completo.
4. **Registro explícito de herramientas.** Cada agente tiene su propio `_TOOL_REGISTRY`; no existe dispatch dinámico ni acceso a herramientas de otros agentes.
5. **Fallback auditable.** Si el LLM no está disponible o no emite tool call, el sistema usa rutas deterministas que producen output observable sin intervención del modelo.

## Justificación de integridad y trazabilidad

- Los identificadores de hallazgos se derivan de `sha256(file_path:line:rule_id)`, garantizando estabilidad y unicidad para correlación entre ciclos.
- El payload final incluye siempre `zero_trust: true` y `mode: proposal_only` como marcadores auditables.
- El campo `errors` en `AgentState` acumula todas las incidencias no fatales, asegurando trazabilidad completa del pipeline.

## Controles OWASP Top 10 cubiertos

| Categoría OWASP | Detección | Remediación propuesta |
|---|---|---|
| A01 – Broken Access Control | `PUBLIC-RESOURCE` (Terraform) | Deshabilitar exposición pública |
| A02 – Cryptographic Failures | `HARDCODED-SECRET` (Python) | Migrar a variable de entorno / vault |
| A03 – Injection | `SQLI-FSTRING`, `SUBPROCESS-SHELL` (Python) | Queries parametrizadas, shell=False |
| A05 – Security Misconfiguration | `RUN-AS-ROOT`, `MISSING-USER` (Docker), `OPEN-CIDR` (Terraform) | Non-root user, CIDR restringido |
| A06 – Vulnerable and Outdated Components | `LATEST-TAG` (Dockerfile) | Pinning a digest inmutable |

## Restricciones operativas del runtime

- El entrypoint de Docker corre como `appuser` (UID 10001), nunca como root.
- El volumen del workspace se monta `:ro` (solo lectura) en Docker Compose.
- `DEVSECOPS_MAX_CYCLES` limita la cantidad de iteraciones para evitar consumo excesivo de recursos.
- La herramienta `run_audit` limita el escaneo a 30 archivos por invocación para prevenir timeouts.

## Protocolo para añadir una nueva regla de auditoría

1. Añadir la lógica de detección en `_scan_file` dentro del tool `run_audit`.
2. Añadir la plantilla de remediación en el dict `_templates` dentro del tool `propose_remediations`.
3. Documentar la nueva regla en la tabla de `doc/agents.md` y en esta sección.
4. Ejecutar `python scripts/validate_packs.py` para verificar que no se rompen compilaciones.

## Protocolo para añadir un nuevo agente

1. Definir el tool del agente con `@tool` y su tipo de retorno.
2. Registrar el tool en `_TOOL_REGISTRY`.
3. Definir el system prompt en `_SYSTEM_PROMPTS`.
4. Implementar la función de fallback determinista en `_deterministic_result`.
5. Añadir las funciones `_build_agent_input` y `_write_agent_output` para el nuevo agente.
6. Añadir el nombre del agente en `workflow_queue` inicial en `run_platform`.
7. Documentar en `doc/agents.md`.
