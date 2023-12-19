from ..registry import action

import os
from github import Github, Issue
from pathlib import Path

# def get_issue_details(repo_url: str, issue_number: int) -> dict:
#     # Retrieve details of the specified issue from the repo
#     pass



@action(
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


@action(
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


@action(
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
    import pprint;
    pprint.pprint("fetch_issue called")
    g = Github(os.environ["GITHUB_TOKEN"])
    print(f"Issue: {owner}/{repo_name}#{issue_id}")
    # Access the repo
    if len(repo_name.split("/")) == 2:
        owner, name = repo_name.split("/")
    else:
        # owner = repo_name
        repo_name = "/".join([owner, repo_name])
    repo = g.get_repo(repo_name)
    # repo = g.get_repo(f"{owner}/{repo_name}")
    pprint.pprint(repo)
    # Fetch the issue by ID
    issue = repo.get_issue(number=issue_id)
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

    ret = f"Issue Title: {issue.title}\nIssue Body: {issue.body}"
    ret += "\nComments:"
    for c in comments:
        ret += f"\n{c.user}: {c.body}"

    return ret


def get_pr_reviews(repo_url: str, pr_number: int) -> list:
    # Fetch reviews and comments for the specified PR
    pass

@action(
    name="add_comment",
    description="Adds a comment to a specified GitHub issue.",
    parameters=[
        {"name": "repo_name", "description": "Name of the repository", "type": "string", "required": True},
        {"name": "owner", "description": "Owner of the repository", "type": "string", "required": True},
        {"name": "issue_number", "description": "Number of the issue", "type": "int", "required": True},
        {"name": "comment_body", "description": "Content of the comment", "type": "string", "required": True},
    ],
    output_type="string",
)

async def add_comment(agent, task_id: str, repo_name: str, owner: str, issue_number: int, comment_body: str) -> str:
    # Create a GitHub instance using a token (You can get the token from your GitHub settings)
    g = Github(os.environ["GITHUB_TOKEN"])
    
    # Get the repository
    if len(repo_name.split("/")) == 2:
        owner, name = repo_name.split("/")
    else:
        owner = repo_name
        repo_name = "/".join([owner, repo_name])
    repo = g.get_repo(repo_name)
    
    # Get the issue
    issue = repo.get_issue(issue_number)
    
    # Add the comment to the issue
    issue.create_comment(comment_body)
    
    return "Successfully added comment to issue."