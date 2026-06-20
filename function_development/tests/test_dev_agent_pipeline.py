from __future__ import annotations

from dataclasses import dataclass

from dev_agent_pipeline import (
    AuditReport,
    AuditorPort,
    ContractReport,
    ContractValidatorPort,
    FunctionRequest,
    GeneratedArtifact,
    PipelineServices,
    PlanArtifact,
    PlannerPort,
    PytestExecutionTool,
    RECURSION_LIMIT,
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
class StubPlanner:
    def plan(self, request: FunctionRequest, stack_context: str, audit_feedback: str | None) -> PlanArtifact:
        return PlanArtifact(
            title=f"Plan for {request.function_name}",
            context_summary=request.specification[:200],
            stack_guidelines_applied=[],
            specifications=request.specification,
            acceptance_criteria=["Function must be implemented as specified.", "All tests must pass."],
            documentation=f"`{request.function_name}` implemented per specification.",
        )


@dataclass(frozen=True)
class StubCoder:
    def generate(self, request: FunctionRequest, attempt: int, feedback: str | None):
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


@dataclass(frozen=True)
class StubContractValidator:
    def validate_contract(self, plan: PlanArtifact, artifact: GeneratedArtifact) -> ContractReport:
        return ContractReport(
            success=True,
            checked_criteria=list(plan.acceptance_criteria),
            failed_criteria=[],
            feedback=None,
        )


@dataclass(frozen=True)
class StubAuditor:
    def audit(
        self,
        plan: PlanArtifact,
        artifact: GeneratedArtifact,
        contract: ContractReport,
        attempt: int,
    ) -> AuditReport:
        return AuditReport(
            approved=contract.success,
            best_practices_violations=[],
            scope_violations=[],
            requires_user_action=False,
            user_action_description=None,
            requires_plan_rework=False,
            feedback=None,
        )


def test_graph_retries_until_validation_passes() -> None:
    graph = build_graph(
        PipelineServices(
            planner=StubPlanner(),
            coder=StubCoder(),
            tester=StubTester(),
            contract_validator=StubContractValidator(),
            auditor=StubAuditor(),
        )
    )
    request = build_request("Implement def add(a: int, b: int) -> int that returns the sum.")
    config = build_runtime_config("test-thread")

    final_state = graph.invoke(build_initial_state(request), config=config)

    assert final_state["attempt"] == 2
    assert final_state["status"] == "completed"
    assert final_state["validation_report"]["success"] is True


def test_runtime_config_uses_fixed_recursion_limit() -> None:
    config = build_runtime_config("thread-123")

    assert config["recursion_limit"] == RECURSION_LIMIT
    assert config["configurable"]["thread_id"] == "thread-123"
