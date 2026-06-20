# Runbook

## 1) Instalación local

```bash
cd devsecops
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .
ollama serve
ollama pull llama3.1
```

## 2) Ejecutar el equipo de agentes sobre un proyecto

```bash
# Auditar el repositorio completo
python devsecops_platform.py /ruta/al/proyecto --show-report

# Con contexto descriptivo
python devsecops_platform.py /ruta/al/proyecto \
  --context "Microservicio Python + Terraform AWS, rama main previo a release" \
  --show-report

# Especificar modelo Ollama diferente
python devsecops_platform.py /ruta --model mistral --show-report
```

## 3) Ejecutar con Docker Compose

```bash
cd devsecops
docker compose up -d ollama
docker compose exec ollama ollama pull llama3.1

# Auditar el directorio raíz del workspace montado en /workspace
docker compose run --rm devsecops /workspace --show-report

# Auditar un subdirectorio específico
docker compose run --rm devsecops /workspace/incident_response --show-report
```

## 4) Variables de entorno

| Variable | Default | Descripción |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.1` | Modelo Ollama a usar |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | URL del servidor Ollama |
| `DEVSECOPS_MAX_CYCLES` | `2` | Número de ciclos de re-auditoría |
| `LOG_LEVEL` | `INFO` | Nivel de logging |

## 5) Interpretar el reporte de salida

### Resumen (siempre impreso)

```json
{
  "target_dir": "/ruta",
  "status": "completed",
  "cycles_completed": 1,
  "threat_intel_count": 4,
  "arch_plan_count": 5,
  "build_proposals_count": 4,
  "deployment_steps_count": 8,
  "audit_findings_count": 3,
  "patches_count": 3,
  "errors": []
}
```

### Reporte completo (`--show-report`)

```json
{
  "zero_trust": true,
  "mode": "proposal_only",
  "threat_intel": [...],
  "arch_plan": [...],
  "build_proposals": [...],
  "deployment_plan": [...],
  "audit_findings": [...],
  "patches": [...]
}
```

### Campos clave

- `audit_findings[].severity`: `critical | high | medium | low`
- `audit_findings[].owasp_top10`: categoría OWASP correspondiente
- `patches[].original_code` / `patched_code`: comparativa del cambio propuesto
- `patches[].vector_prevented`: vector de ataque que la mitigación cierra
- `deployment_plan[].risk`: nivel de riesgo del paso de despliegue
- `deployment_plan[].rollback`: comando de reversión si el paso falla

## 6) Modo offline (sin Ollama)

El sistema funciona completamente sin Ollama gracias al fallback determinista. Cada agente ejecuta sus herramientas directamente y produce output estructurado válido. Para uso en CI/CD offline:

```bash
# Port 0 is unassignable; this forces Ollama connection to fail and activates deterministic fallback mode.
OLLAMA_HOST=http://127.0.0.1:0 python devsecops_platform.py /ruta --show-report
```

El sistema detecta que Ollama no está disponible y opera en modo determinista automáticamente.

## 7) Integración en CI/CD

```yaml
# Ejemplo GitHub Actions
- name: DevSecOps Platform Audit
  run: |
    pip install -e ./devsecops
    python ./devsecops/devsecops_platform.py . --show-report > devsecops-report.json
    
- name: Upload report
  uses: actions/upload-artifact@v3
  with:
    name: devsecops-report
    path: devsecops-report.json
```
