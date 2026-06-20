# Security

## Operational boundaries

- The pack is analysis-only; it does not execute code, create files, or make network calls beyond Ollama.
- All agents produce text outputs and structured analysis only.
- Debate state is persisted through `MemorySaver` for local checkpointing; no external storage is used.

## Input handling

- Project descriptions are passed directly to the LLM inside a structured JSON payload.
- Operators should avoid including credentials, personal data, or sensitive internal details in the `--input` field.
- The `--input` value is not sanitised beyond Python string stripping; operators are responsible for content.

## Prompt and output safety

- All agent prompts are scoped to analysis tasks (requirements, technology, evaluation, audit).
- Agents that return JSON use Pydantic models (`RequirementsAnalysis`, `TechAndPlanProposal`, `ProjectEvaluation`, `CompletionAudit`, `QAReview`) to validate and bound the output before it is used.
- Invalid or malformed LLM output triggers deterministic fallback logic that never raises an unhandled exception.

## Consensus safety controls

- `max_rounds` is bounded to `1..3` by `run_lifecycle`.
- QA is auto-approved when `round_number >= max_rounds` to guarantee graph termination.
- `recursion_limit=30` provides a graph-level guard against accidental infinite loops.

## Failure handling

- Ollama connection and timeout failures are captured as non-fatal warnings in `errors`.
- Each agent has a deterministic fallback that produces reasonable output without the LLM.
- `finalizer` always emits one complete Markdown document, even when all agents used fallback mode.

## Mode boundaries

- `define` mode: reads project descriptions, produces documentation. Does not access the filesystem except via the `--output` flag.
- `evaluate` mode: reads project descriptions, produces evaluation reports. No filesystem or network access beyond Ollama.
- `audit` mode: reads project descriptions, produces audit reports. No filesystem or network access beyond Ollama.
