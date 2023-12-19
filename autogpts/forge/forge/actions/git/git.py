from ..registry import action

import os
# import forge.actions.git.git as git
# from forge.actions.git.git import Repo
# from pathlib import Path

# from github import Github
import git
from git import Repo

from ...agent import Agent


# @action(
#     name="create_pull_request",
#     description="Creates a pull request on GitHub to merge the head branch into the base branch.",
#     parameters=[
#         {"name": "title", "description": "Title of the pull request", "type": "string", "required": True},
#         {"name": "body", "description": "Description/body of the pull request", "type": "string", "required": True},
#         {"name": "repo_name", "description": "Name of the repository in owner/repo format. The repo at https://github.com/runyontr/docs would be provided as 'runyontr/docs'", "type": "string", "required": True},
#         {"name": "base_branch", "description": "Branch the changes will be merged into", "type": "string", "required": True},
#         {"name": "head_branch", "description": "Branch where your changes are", "type": "string", "required": True},
#     ],
#     output_type="string",
# )
# async def create_pull_request(agent, task_id: str, repo_name: str, title: str, body: str, base_branch: str, head_branch: str) -> str:
#     # Logic for creating a pull request goes here
#     try:
#         g = Github(os.environ["GITHUB_TOKEN"])
#         repo = g.get_repo(repo_name)
#         pr = repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
#         return pr.html_url
#     except Exception as e:
#         print(f"Error creating pull request: {e}")
#         return str(f"{e}")
#     return "Successfully created pull request."


@action(
    name="clone_repo",
    description="Clones a GitHub repository into the dest_path folder which it expects not to exist. This will fail if that folder is already present",
    parameters=[
        {"name": "repo_url", "description": "URL of the GitHub repository", "type": "string", "required": True},
        {"name": "dest_path", "description": "Local destination path.  If empty it defaults to a local folder matching the git repository name", "type": "string", "required": False},
    ],
    output_type="string",
)
async def clone_repo(agent: Agent, task_id: str, repo_url: str, dest_path: str) -> str:
    
    if dest_path is None:
        # set dest path to the last part of the repo url
        dest_path = repo_url.split("/")[-1]

    try:
        # Retrieve the GitHub token from an environment variable
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return "GitHub token not found in environment variables."

        # Convert the repo URL to include the token for authentication
        repo_url_with_token = repo_url.replace("https://", f"https://{token}@")

        # Clone the repository
        # agent.workspace.list(task_id=task_id, path=".")
        # set the path to download the repo to to be the dest_path inside of os.getenv("AGENT_WORKSPACE")
        dest = agent.workspace.base_path / task_id / dest_path

        Repo.clone_from(repo_url_with_token, dest)

        return f"Successfully cloned repository to {dest}."
    except git.GitCommandError as e:
        return f"Error cloning repository: {str(e)}"



@action(
    name="create_branch",
    description="Creates a new branch in the repository.",
    parameters=[
        {"name": "branch_name", "description": "Name of the new branch", "type": "string", "required": True},
        {"name": "base_branch", "description": "Base branch for the new branch", "type": "string", "required": False, "default": "main"},
        {"name": "repo_path", "description": "Path to the local repository", "type": "string", "required": True}
    ],
    output_type="string",
)
async def create_branch(agent, task_id: str, repo_path: str,  branch_name: str, base_branch: str = 'main') -> str:
    # Load the repository
    try:
        print(f"in create_branch")
        repo_path = agent.workspace.base_path / task_id / repo_path
        print(f"repo path: {repo_path}")
        repo = Repo(repo_path)
        print(f"Created repo: {repo}")
        print(f"Current branch {repo.active_branch.name} branch")
        # might also want to check if the branch already exists
        repo.git.checkout("HEAD", b=branch_name)
        #  new_branch = repo.create_head(branch_name, "HEAD")  # create a new branch ...
        print(f"Created branch: {branch_name}")
        print(f"Current branch {repo.active_branch.name} branch")
        return f"Successfully created branch {branch_name} from {base_branch}"
    except git.GitCommandError as e:
        return f"Error creating branch: {str(e)}"
    except Exception as e:
        return f"Error creating branch: {str(e)}"

@action(
    name="commit_changes",
    description="Commits changes made in the current branch.",
    parameters=[
        {"name": "commit_message", "description": "Message for the commit", "type": "string", "required": True},
        {"name": "repo_path", "description": "Path to the local repository", "type": "string", "required": True}
    ],
    output_type="string",
)
async def commit_changes(agent, task_id: str, commit_message: str, repo_path: str) -> str:
    try:
        # Load the repository
        repo_path = agent.workspace.base_path / task_id / repo_path
        
        repo = Repo(repo_path)
        
        # Check for changes
        if not repo.is_dirty() and repo.untracked_files == []:
            return "No changes to commit."

        # Add all changed files
        repo.git.add(A=True)

        for file in repo.untracked_files:
            repo.git.add(file)
        
        # Commit the changes
        repo.git.commit(m=commit_message)

        return f"Successfully committed changes with message: {commit_message}"
    except git.GitCommandError as e:
        return f"Error committing changes: {str(e)}"


@action(
    name="push_branch",
    description="Pushes the current branch to the specified remote.",
    parameters=[
        {"name": "branch_name", "description": "Name of the branch to push", "type": "string", "required": True},
        {"name": "remote_name", "description": "Name of the remote (default is 'origin')", "type": "string", "required": False, "default": "origin"},
        {"name": "repo_path", "description": "Path to the local repository", "type": "string", "required": True}
    ],
    output_type="string",
)
async def push_branch(agent, task_id: str, repo_path: str, branch_name: str, remote_name: str = 'origin') -> str:
    # Logic for pushing branch goes here
    try:
        repo_path = agent.workspace.base_path / task_id / repo_path
        
        repo = git.Repo(repo_path)
        remote = repo.remote(name=remote_name)
        remote.push(refspec=branch_name)
        print(f"Successfully pushed branch '{branch_name}' to remote '{remote_name}'!")
    except git.exc.GitCommandError as e:
        print(f"Error pushing branch to remote: {e}")
    return "Successfully pushed branch."




