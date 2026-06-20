# DevSecOps Platform Pack

Pack multi-agente local en Python que actúa como un equipo DevSecOps completo: investiga amenazas, planifica arquitectura, genera infraestructura segura, propone despliegues, audita continuamente y remedia hallazgos — todo bajo política Zero Trust.

## Agentes del equipo

| Agente | Rol |
|---|---|
| **Orchestrator** | Coordina el flujo entre agentes; decide ciclos de re-auditoría |
| **ThreatIntel** | Investiga CVEs, advisories cloud y novedades OWASP |
| **Architect** | Traduce amenazas en plan técnico priorizado |
| **Builder** | Genera Terraform, Dockerfiles, K8s manifests y políticas OPA |
| **Deployment** | Crea plan de despliegue paso a paso con rollback seguro |
| **Auditor** | Ejecuta SAST e IaC audit (Python, Dockerfile, Terraform) |
| **Remediator** | Propone parches de código y configuración por cada hallazgo |

## Quick start

```bash
cd devsecops
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .
ollama serve && ollama pull llama3.1
python devsecops_platform.py . --show-report
```

Docker Compose:

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
docker compose run --rm devsecops /workspace --show-report
```

## Operación

```
devsecops_platform.py <target_dir> [--context "descripción"] [--show-report] [--model llama3.1]
```

- `target_dir`: directorio raíz del proyecto a auditar.
- `--show-report`: imprime el reporte JSON completo (proposal_only).
- `DEVSECOPS_MAX_CYCLES`: variable de entorno para número de ciclos (default `2`).

## Documentación

| Documento | Descripción |
|---|---|
| [doc/agents.md](doc/agents.md) | Contratos, entradas y salidas de cada agente |
| [doc/architecture.md](doc/architecture.md) | Estado compartido, flujo y diagrama Mermaid |
| [doc/runbook.md](doc/runbook.md) | Instalación, ejecución, Docker y lectura de reportes |
| [doc/security.md](doc/security.md) | Política Zero Trust, controles y justificación |
