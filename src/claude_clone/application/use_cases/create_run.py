"""CreateRunUseCase - Create a new agent run."""

from dataclasses import dataclass
from typing import Optional

from claude_clone.domain.entities.run import Run
from claude_clone.domain.entities.event import EventType
from claude_clone.application.interfaces.run_repository import RunRepository
from claude_clone.application.interfaces.event_publisher import EventPublisher


@dataclass
class CreateRunRequest:
    """Request to create a new run."""

    goal: str
    repo_root: str = "."
    branch: Optional[str] = None


@dataclass
class CreateRunResponse:
    """Response from creating a run."""

    run_id: str
    status: str


class CreateRunUseCase:
    """Use case: Create a new agent run.

    Steps:
    1. Create Run entity
    2. Save to repository
    3. Publish run.started event
    4. Return response
    """

    def __init__(
        self,
        run_repository: RunRepository,
        event_publisher: EventPublisher,
    ):
        self.run_repository = run_repository
        self.event_publisher = event_publisher

    def execute(self, request: CreateRunRequest) -> CreateRunResponse:
        """Execute the use case."""
        # Create run entity
        run = Run.create(goal=request.goal, repo_root=request.repo_root)
        if request.branch:
            run.branch = request.branch

        # Start the run
        run.start()

        # Save to repository
        self.run_repository.save(run)

        # Publish event
        self.event_publisher.publish(
            run_id=run.id,
            event_type=EventType.RUN_STARTED,
            data={"goal": run.goal, "repo_root": run.repo_root},
        )

        return CreateRunResponse(
            run_id=run.id,
            status=run.status.value,
        )
