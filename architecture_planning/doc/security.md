# Security

## Operational boundaries

- The pack is planning-only; it does not execute infrastructure changes.
- Agents produce text outputs and structured risk analysis only.
- Debate state is persisted through `MemorySaver` for local checkpointing.

## Prompt and output safety

- Architect prompt is constrained to topology, data strategy, cache, and consistency topics.
- QA prompt forces strict JSON output for deterministic parsing (`QAAudit`).
- Invalid or malformed QA output triggers deterministic fallback audit logic.

## Consensus safety controls

- `max_rounds` is bounded to `1..3`.
- Debate loop terminates on explicit QA approval or round-cap exhaustion.
- `recursion_limit=20` adds a graph-level protection against accidental infinite loops.

## Failure handling

- Ollama failures are captured as warnings in `errors`.
- Fallback proposal and fallback audit keep the workflow operational during model outages.
- Finalization always emits one technical Markdown document, even in fallback mode.
