
import base64
from typing import Any

import httpx2
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel

mcp = MCPServer("devpilot-github")

GITHUB_API_BASE = "https://api.github.com"
USER_AGENT = "DevPilot-AI/1.0"

GITHUB_TOOL_ANNOTATIONS = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)


# -------------------- OUTPUT MODELS --------------------

class RepositoryInfo(BaseModel):
    name: str
    full_name: str
    description: str
    language: str
    stars: int
    forks: int
    default_branch: str
    url: str


class RepositoryFile(BaseModel):
    name: str
    path: str
    type: str
    url: str


class RepositoryFiles(BaseModel):
    items: list[RepositoryFile]


class RepositoryFileContent(BaseModel):
    file_name: str
    file_path: str
    content: str
    language: str


class RepositoryIssue(BaseModel):
    number: int
    title: str
    state: str
    author: str
    body: str
    labels: list[str]
    url: str
    created_at: str


class RepositoryIssues(BaseModel):
    issues: list[RepositoryIssue]


class RepositoryPullRequest(BaseModel):
    number: int
    title: str
    state: str
    author: str
    body: str
    source_branch: str
    target_branch: str
    url: str
    created_at: str


class RepositoryPullRequests(BaseModel):
    pull_requests: list[RepositoryPullRequest]


class RepositoryCommit(BaseModel):
    sha: str
    message: str
    author: str
    date: str
    url: str


class RepositoryCommits(BaseModel):
    commits: list[RepositoryCommit]


# -------------------- GITHUB API HELPER --------------------

async def make_github_request(endpoint: str) -> Any:
    """Make a request to the GitHub REST API."""

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
    }

    async with httpx2.AsyncClient() as client:
        try:
            response = await client.get(
                f"{GITHUB_API_BASE}{endpoint}",
                headers=headers,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

        except httpx2.HTTPStatusError as error:
            raise ToolError(
                f"GitHub API returned status {error.response.status_code}."
            ) from error

        except Exception as error:
            raise ToolError(
                f"GitHub request failed: {error}"
            ) from error


# -------------------- TOOL 1: REPOSITORY INFORMATION --------------------

@mcp.tool(annotations=GITHUB_TOOL_ANNOTATIONS)
async def get_repository_info(owner: str, repo: str) -> RepositoryInfo:
    """Get information about a public GitHub repository.

    Args:
        owner: GitHub username or organisation.
        repo: Repository name.
    """

    data = await make_github_request(f"/repos/{owner}/{repo}")

    return RepositoryInfo(
        name=data["name"],
        full_name=data["full_name"],
        description=data.get("description") or "No description available",
        language=data.get("language") or "Not specified",
        stars=data["stargazers_count"],
        forks=data["forks_count"],
        default_branch=data["default_branch"],
        url=data["html_url"],
    )


# -------------------- TOOL 2: LIST REPOSITORY FILES --------------------

@mcp.tool(annotations=GITHUB_TOOL_ANNOTATIONS)
async def list_repository_files(
    owner: str,
    repo: str,
    path: str = "",
) -> RepositoryFiles:
    """List files and directories in a public GitHub repository.

    Args:
        owner: GitHub username or organisation.
        repo: Repository name.
        path: Directory path inside the repository. Leave empty for root.
    """

    endpoint = f"/repos/{owner}/{repo}/contents"

    if path:
        endpoint += f"/{path}"

    data = await make_github_request(endpoint)

    if isinstance(data, dict):
        data = [data]

    return RepositoryFiles(
        items=[
            RepositoryFile(
                name=item["name"],
                path=item["path"],
                type=item["type"],
                url=item["html_url"],
            )
            for item in data
        ]
    )


# -------------------- TOOL 3: READ SOURCE FILES --------------------

@mcp.tool(annotations=GITHUB_TOOL_ANNOTATIONS)
async def read_repository_file(
    owner: str,
    repo: str,
    path: str,
) -> RepositoryFileContent:
    """Read a file from a public GitHub repository.

    Args:
        owner: GitHub username or organisation.
        repo: Repository name.
        path: Path of the file inside the repository.
    """

    data = await make_github_request(
        f"/repos/{owner}/{repo}/contents/{path}"
    )

    if data.get("type") != "file":
        raise ToolError("The requested path is not a file.")

    if data.get("encoding") != "base64":
        raise ToolError(
            "Unsupported file encoding. The file may be too large."
        )

    try:
        content = base64.b64decode(
            data["content"]
        ).decode("utf-8", errors="replace")

    except (KeyError, ValueError) as error:
        raise ToolError(
            "Unable to decode the requested file."
        ) from error

    file_name = data["name"]

    language = (
        file_name.rsplit(".", 1)[-1]
        if "." in file_name
        else "unknown"
    )

    return RepositoryFileContent(
        file_name=file_name,
        file_path=data["path"],
        content=content,
        language=language,
    )


# -------------------- TOOL 4: GET REPOSITORY ISSUES --------------------

@mcp.tool(annotations=GITHUB_TOOL_ANNOTATIONS)
async def get_repository_issues(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> RepositoryIssues:
    """Get issues from a public GitHub repository.

    Args:
        owner: GitHub username or organisation.
        repo: Repository name.
        state: Issue state: open, closed or all.
        limit: Maximum number of issues to retrieve (1-30).
    """

    if state not in {"open", "closed", "all"}:
        raise ToolError("State must be open, closed or all.")

    if not 1 <= limit <= 30:
        raise ToolError("Limit must be between 1 and 30.")

    data = await make_github_request(
        f"/repos/{owner}/{repo}/issues"
        f"?state={state}&per_page={limit}"
    )

    issues = [
        RepositoryIssue(
            number=item["number"],
            title=item["title"],
            state=item["state"],
            author=item["user"]["login"],
            body=item.get("body") or "No description provided.",
            labels=[label["name"] for label in item.get("labels", [])],
            url=item["html_url"],
            created_at=item["created_at"],
        )
        for item in data
        if "pull_request" not in item
    ]

    return RepositoryIssues(issues=issues)


# -------------------- TOOL 5: GET PULL REQUESTS --------------------

@mcp.tool(annotations=GITHUB_TOOL_ANNOTATIONS)
async def get_repository_pull_requests(
    owner: str,
    repo: str,
    state: str = "open",
    limit: int = 10,
) -> RepositoryPullRequests:
    """Get pull requests from a public GitHub repository.

    Args:
        owner: GitHub username or organisation.
        repo: Repository name.
        state: Pull request state: open, closed or all.
        limit: Maximum number of pull requests to retrieve (1-30).
    """

    if state not in {"open", "closed", "all"}:
        raise ToolError("State must be open, closed or all.")

    if not 1 <= limit <= 30:
        raise ToolError("Limit must be between 1 and 30.")

    data = await make_github_request(
        f"/repos/{owner}/{repo}/pulls"
        f"?state={state}&per_page={limit}"
    )

    pull_requests = [
        RepositoryPullRequest(
            number=item["number"],
            title=item["title"],
            state=item["state"],
            author=item["user"]["login"],
            body=item.get("body") or "No description provided.",
            source_branch=item["head"]["ref"],
            target_branch=item["base"]["ref"],
            url=item["html_url"],
            created_at=item["created_at"],
        )
        for item in data
    ]

    return RepositoryPullRequests(
        pull_requests=pull_requests
    )


# -------------------- TOOL 6: GET COMMIT HISTORY --------------------

@mcp.tool(annotations=GITHUB_TOOL_ANNOTATIONS)
async def get_repository_commits(
    owner: str,
    repo: str,
    limit: int = 10,
) -> RepositoryCommits:
    """Get recent commits from a public GitHub repository.

    Args:
        owner: GitHub username or organisation.
        repo: Repository name.
        limit: Number of recent commits to retrieve (1-30).
    """

    if not 1 <= limit <= 30:
        raise ToolError("Limit must be between 1 and 30.")

    data = await make_github_request(
        f"/repos/{owner}/{repo}/commits?per_page={limit}"
    )

    commits = [
        RepositoryCommit(
            sha=item["sha"],
            message=item["commit"]["message"],
            author=(
                item["commit"]["author"]["name"]
                if item["commit"].get("author")
                else "Unknown"
            ),
            date=(
                item["commit"]["author"]["date"]
                if item["commit"].get("author")
                else "Unknown"
            ),
            url=item["html_url"],
        )
        for item in data
    ]

    return RepositoryCommits(commits=commits)


# -------------------- START MCP SERVER --------------------

def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
