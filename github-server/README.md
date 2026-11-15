# DevPilot AI — GitHub MCP Server

A Python MCP server that exposes read-only GitHub repository information and activity as tools for an MCP-compatible client.

## Available tools

- `get_repository_info`
- `list_repository_files`
- `read_repository_file`
- `get_repository_issues`
- `get_repository_pull_requests`
- `get_repository_commits`

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

## Run

From the `mcp-client-python` directory, launch the server through the client:

```bash
uv run client.py uv --directory ../github-server run github_server.py
```

To run the server directly:

```bash
uv run github_server.py
```

The server uses stdio transport and waits for an MCP client when run directly.

## Scope

The current tools read data from public GitHub repositories. They do not create, edit, or delete GitHub resources.

## Attribution

Adapted from the Python server example in the [Model Context Protocol Quickstart Resources](https://github.com/modelcontextprotocol/quickstart-resources), with GitHub-specific project modifications. Retain and follow the original license and attribution requirements.
