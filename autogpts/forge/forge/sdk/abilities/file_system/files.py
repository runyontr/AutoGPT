import pprint
from typing import List

from ..registry import ability
from ....sdk import (
    PromptEngine,
    chat_completion_request,
)
import json

@ability(
    name="list_files",
    description="List files in a directory and return a list of their names including the path parameter",
    parameters=[
        {
            "name": "path",
            "description": "Path to the directory",
            "type": "string",
            "required": True,
        }
    ],
    output_type="list[str]",
)
async def list_files(agent, task_id: str, path: str) -> List[str]:
    """
    List files in a workspace directory
    """
    return agent.workspace.list(task_id=task_id, path=str(path))


@ability(
    name="write_file",
    description="Write data to a file",
    parameters=[
        {
            "name": "file_path",
            "description": "Path to the file",
            "type": "string",
            "required": True,
        },
        {
            "name": "data",
            "description": "Data to write to the file",
            "type": "bytes",
            "required": True,
        },
    ],
    output_type="None",
)
async def write_file(agent, task_id: str, file_path: str, data: bytes):
    """
    Write data to a file
    """
    if isinstance(data, str):
        data = data.encode()

    agent.workspace.write(task_id=task_id, path=file_path, data=data)
    return await agent.db.create_artifact(
        task_id=task_id,
        file_name=file_path.split("/")[-1],
        relative_path=file_path,
        agent_created=True,
    )


@ability(
    name="read_file",
    description="Read data from a file",
    parameters=[
        {
            "name": "file_path",
            "description": "Path to the file",
            "type": "string",
            "required": True,
        },
    ],
    output_type="bytes",
)
async def read_file(agent, task_id: str, file_path: str) -> bytes:
    """
    Read data from a file
    """
    print(f"Task {task_id}: looking to read { file_path }")
    return agent.workspace.read(task_id=task_id, path=file_path)


@ability(
    name="modify_file",
    description="Return an updated file contents with the changes requested applied.",
    parameters=[
        {
            "name": "file_path",
            "description": "Path to the file",
            "type": "string",
            "required": True,
        },
        {
            "name": "changes_requested",
            "description": "description of the changes requested to the file. This is normally the task text that is provided.",
            "type": "string",
            "required": True,
        },
    ],
    output_type="string",
)
async def modify_file(agent, task_id: str, file_path: str, changes_requested: str) -> str:
    # Make specified changes to the given file in the local repo
    # we might want this to be a gpt-4 call to improve performance.
    prompt_engine = PromptEngine("gpt-3.5-turbo")

    contents = await read_file(agent,task_id=task_id ,file_path=file_path)
    if contents is None:
        return None
    task_kwargs = {
                "issue_text": changes_requested,
                "file": str(contents),
            }

    prompt = prompt_engine.load_prompt("suggested_file_change", **task_kwargs)
    print(f"modify_file: Prompt for modifying file is {prompt}")
    # Initialize the messages list with the system prompt
    messages = [
        {"role": "system", "content": "Reply only with the modified file contents and nothing else.  Take a deep breath before starting and ensure the changes address the issue in a clear and concise manner."},
    ]
    messages.append({"role": "user", "content": prompt})

    chat_completion_kwargs = {
                "messages": messages,
                "model": "gpt-3.5-turbo",
            }
    chat_response = await chat_completion_request(**chat_completion_kwargs)
    pprint.pprint(f"Response:\n\n{chat_response}")
    # answer = json.loads(chat_response["choices"][0]["message"]["content"])
    answer = chat_response["choices"][0]["message"]["content"]
    pprint.pprint(f"Updated file:\n\n{answer}")
    #XXX update the prompt to remove the markdown prompt
    # Need to unwrap to write the file with actual new lines

    x = await write_file(agent, task_id=task_id, file_path=file_path, data=answer)

    return x

