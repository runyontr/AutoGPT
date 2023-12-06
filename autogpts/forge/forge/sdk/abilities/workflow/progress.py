
from ..registry import ability


@ability(
    name="cant_make_progress",
    description="Should be called when the agent doesn't believe it can make any progress on the task",
    parameters=[
        {"name": "reason", "description": "Explination for why the agent cannot make any progress", "type": "string", "required": True},
        {"name": "new_ability", "description": "Suggestion for a new ability, that if provided to the agent, would allow for progress to be made", "type": "string", "required": False},
    ],
    output_type="dict",
)
async def fetch_issue(agent, task_id: str, reason: str, new_ability: str) -> str: {
    print(f"Task {task_id} cannot make any more progress: {reason}")
}