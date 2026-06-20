from __future__ import annotations

from dataclasses import dataclass

from dev_agent_pipeline import (
    GeneratedArtifact,
    PipelineServices,
    PytestExecutionTool,
    TesterAgent as PipelineTesterAgent,
    ValidationReport,
    build_graph,
    build_initial_state,
    build_request,
    build_runtime_config,
    infer_function_name,
)


def test_infer_function_name_prefers_signature() -> None:
    specification = "Implement def clamp(value: int, lower: int, upper: int) -> int that bounds value."

    assert infer_function_name(specification) == "clamp"


def test_tester_blocks_unsafe_code_before_pytest() -> None:
    artifact = GeneratedArtifact(
        function_name="dangerous",
        function_code="import os\n\ndef dangerous() -> None:\n    os.system('echo nope')\n",
        test_code="from subject import dangerous\n\ndef test_placeholder() -> None:\n    dangerous()\n",
    )

    report = PipelineTesterAgent().validate(artifact)

    assert report.success is False
    assert report.blocked_reason is not None
    assert "os.system" in report.blocked_reason


def test_pytest_execution_tool_returns_traceback_feedback() -> None:
    artifact = GeneratedArtifact(
        function_name="add",
        function_code="def add(a: int, b: int) -> int:\n    return a - b\n",
        test_code=(
            "from subject import add\n\n"
            "def test_add() -> None:\n"
            "    assert add(2, 3) == 5\n"
        ),
    )

    report = PytestExecutionTool().run(artifact)

    assert report.success is False
    assert report.exit_code == 1
    assert report.feedback is not None
    assert "assert -1 == 5" in report.feedback


@dataclass(frozen=True)
class StubCoder:
    def generate(self, request, attempt: int, feedback: str | None):
        if attempt == 1:
            return GeneratedArtifact(
                function_name=request.function_name,
                function_code="def add(a: int, b: int) -> int:\n    return a - b\n",
                test_code="from subject import add\n\ndef test_add() -> None:\n    assert add(2, 3) == 5\n",
            )
        return GeneratedArtifact(
            function_name=request.function_name,
            function_code="def add(a: int, b: int) -> int:\n    return a + b\n",
            test_code="from subject import add\n\ndef test_add() -> None:\n    assert add(2, 3) == 5\n",
        )


@dataclass(frozen=True)
class StubTester:
    def validate(self, artifact: GeneratedArtifact) -> ValidationReport:
        if "return a + b" in artifact.function_code:
            return ValidationReport(success=True, exit_code=0, stdout="1 passed", stderr="")
        return ValidationReport(success=False, exit_code=1, stdout="", stderr="", feedback="assert -1 == 5")


def test_graph_retries_until_validation_passes() -> None:
    graph = build_graph(PipelineServices(coder=StubCoder(), tester=StubTester()))
    request = build_request("Implement def add(a: int, b: int) -> int that returns the sum.")
    config = build_runtime_config("test-thread")

    final_state = graph.invoke(build_initial_state(request), config=config)

    assert final_state["attempt"] == 2
    assert final_state["status"] == "completed"
    assert final_state["validation_report"]["success"] is True


def test_runtime_config_uses_fixed_recursion_limit() -> None:
    config = build_runtime_config("thread-123")

    assert config["recursion_limit"] == 8
    assert config["configurable"]["thread_id"] == "thread-123"
