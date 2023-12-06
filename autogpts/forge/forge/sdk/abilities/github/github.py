from ..registry import ability

import os
import git
from git import Repo
from github import Github, Issue
from pathlib import Path

from ...agent import Agent

# def get_issue_details(repo_url: str, issue_number: int) -> dict:
#     # Retrieve details of the specified issue from the repo
#     pass



@ability(
    name="create_pull_request",
    description="Creates a pull request on GitHub to merge the head branch into the base",
    parameters=[
        {"name": "title", "description": "Title of the pull request", "type": "string", "required": True},
        {"name": "body", "description": "Description/body of the pull request", "type": "string", "required": True},
        {"name": "repo_name", "description": "Name of the repository in owner/repo format. The repo at https://github.com/runyontr/docs would be provided as 'runyontr/docs'", "type": "string", "required": True},
        {"name": "base_branch", "description": "Branch the changes will be merged into", "type": "string", "required": True},
        {"name": "head_branch", "description": "Branch where your changes are", "type": "string", "required": True},
    ],
    output_type="string",
)
async def create_pull_request(agent, task_id: str, repo_name: str, title: str, body: str, base_branch: str, head_branch: str) -> str:
    # Logic for creating a pull request goes here
    try:
        g = Github(os.environ["GITHUB_TOKEN"])
        repo = g.get_repo(repo_name)
        pr = repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
        return pr.html_url
    except Exception as e:
        print(f"Error creating pull request: {e}")
        return str(f"{e}")
    return "Successfully created pull request."


@ability(
    name="fetch_issues",
    description="Fetches issues from a GitHub repository.",
    parameters=[
        {"name": "repo_name", "description": "Name of the repository", "type": "string", "required": True},
        {"name": "owner", "description": "Owner of the repository", "type": "string", "required": True},
        {"name": "labels", "description": "Labels to filter issues by", "type": "list", "required": False},
        {"name": "state", "description": "State of issues ('open', 'closed')", "type": "string", "required": False, "default": "open"},
    ],
    output_type="list",
)
async def fetch_issues(agent, task_id: str, repo_name: str, owner: str, labels: list = None, state: str = 'open') -> list:
    # Logic to fetch issues from GitHub goes here
    return []


@ability(
    name="fetch_issue",
    description="Fetches a single issue from a GitHub repository using Issue ID.",
    parameters=[
        {"name": "repo_name", "description": "Name of the repository.  Should not include the owner", "type": "string", "required": True},
        {"name": "owner", "description": "Owner of the repository", "type": "string", "required": True},
        {"name": "issue_id", "description": "ID of the issue to fetch", "type": "int", "required": True},
    ],
    output_type="Issue",
)
async def fetch_issue(agent, task_id: str, repo_name: str, owner: str, issue_id: int) -> Issue:
    # Logic to fetch a single issue from GitHub using Issue ID goes here
        # Create a GitHub instance using a token (You can get the token from your GitHub settings)
    # Make sure the token has appropriate permissions to access issues.
    g = Github(os.environ["GITHUB_TOKEN"])

    # Access the repo
    repo = g.get_repo(f"{owner}/{repo_name}")

    # Fetch the issue by ID
    issue = repo.get_issue(number=issue_id)
    import pprint;
    print(f"Issue: {owner}/{repo_name}#{issue_id}")
    pprint.pprint(issue)
    # return Issue
    comments = issue.get_comments()
    print(f"Comments: \n")
    for c in comments:
        print(f"{c.issue_url}:\n {c.user}: {c.body}\n")
    pprint.pprint(comments)
    # Extract relevant information from the issue object to return as a dictionary
    issue_data = {
        "id": issue.id,
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
        "state": issue.state,
        "created_at": issue.created_at,
        "updated_at": issue.updated_at,
        "user": {
            "login": issue.user.login,
            "avatar_url": issue.user.avatar_url,
            "html_url": issue.user.html_url
        },
        # comments on the issue
        "comments": [ {"user": c.user.login, "body": c.body, "id": c.id}  for c in comments]
    }

    return issue_data


def get_pr_reviews(repo_url: str, pr_number: int) -> list:
    # Fetch reviews and comments for the specified PR
    pass
