# Runbook

## 1) Preparación local

```bash
cd devsecops_audit
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .
ollama serve
ollama pull llama3.1
```

## 2) Ejecutar auditoría sobre archivo inseguro

### Python

```bash
python devsecops_auditor.py /abs/path/script_inseguro.py --show-history
```

### Dockerfile

```bash
python devsecops_auditor.py /abs/path/Dockerfile --show-history
```

### Terraform

```bash
python devsecops_auditor.py /abs/path/main.tf --show-history
```

## 3) Interpretar el reporte de mitigación

La salida JSON incluye:

- `vulnerability_count`: total de hallazgos detectados.
- `patch_count`: total de parches propuestos.
- `errors`: incidencias no fatales del pipeline.
- `mitigation_payload`: propuesta Zero Trust con:
  - `vulnerabilities`: detalle técnico de riesgo.
  - `secure_patches`: diff sugerido por vulnerabilidad.
  - `risk_summary`: resumen ejecutivo de mitigaciones.

## 4) Operación con Docker Compose

```bash
cd devsecops_audit
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1
docker compose run --rm devsecops-auditor /workspace/incident_response/app_multi_agent.py --show-history
```
