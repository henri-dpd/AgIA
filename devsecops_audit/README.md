# DevSecOps SAST/IaC Auditor Pack

Pack multi-agente local en Python para auditoría de código estática (SAST) y análisis de Infraestructura como Código (IaC) con LangGraph y Ollama.

## SECCIÓN 1: Implementación del script completo de Python con LangGraph (`devsecops_auditor.py`)

La implementación completa está en [`devsecops_auditor.py`](devsecops_auditor.py) e incluye:

- Grafo `StateGraph` con dos nodos: `analyzer` y `mitigator`.
- Estado tipado `AgentState` con acumulación de `vulnerabilities` y `secure_patches`.
- Simulación de análisis estático para Python, Dockerfile y Terraform.
- Generación de payload de mitigación en JSON bajo política Zero Trust (`proposal_only`).
- Integración con Ollama optimizada para `tool calling` y fallback determinista.

## SECCIÓN 2: Documentación Técnica y de Mantenimiento

- Estructuras de datos y contratos de agentes: [doc/agents.md](doc/agents.md)
- Arquitectura, estado y diagrama Mermaid: [doc/architecture.md](doc/architecture.md)
- Controles de seguridad y justificación criptográfica/Zero Trust: [doc/security.md](doc/security.md)

## SECCIÓN 3: Manual de uso y operación

El manual operativo completo está en [doc/runbook.md](doc/runbook.md), incluyendo:

- Cómo apuntar el agente a un `Dockerfile`, `*.py` o `*.tf` inseguro.
- Cómo interpretar el reporte de mitigación y el payload JSON propuesto.
- Ejecución local y vía Docker Compose.
