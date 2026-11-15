# DevPilot AI

**An MCP-powered GitHub Repository Intelligence Assistant**

DevPilot AI connects a Python MCP client to a GitHub MCP server and uses Google Gemini to help developers explore public GitHub repositories through natural-language questions.

## Features

The GitHub MCP server currently exposes six read-only tools:

- **Repository information** — view repository metadata such as description, language, stars, forks and default branch.
- **List repository files** — browse files and directories.
- **Read repository files** — retrieve the contents of supported text files.
- **Repository issues** — inspect issues and their details.
- **Pull requests** — inspect pull requests, branches and status.
- **Recent commits** — review recent commit messages and authors.

## Architecture

```text
User
 |
 v
Python MCP Client  <---->  Google Gemini
 |
 | MCP over stdio
 v
GitHub MCP Server
 |
 | GitHub REST API
 v
Public GitHub Repositories
```

The client discovers the tools exposed by the MCP server and makes them available to Gemini. Gemini can request tool calls, and the client executes those calls through the MCP connection.

## Project structure

```text
devpilot/
├── mcp-client-python/
│   ├── client.py
│   ├── pyproject.toml
│   └── README.md
├── github-server/
│   ├── github_server.py
│   ├── pyproject.toml
│   └── README.md
└── README.md
```

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- A Google Gemini API key

## Setup

### 1. Configure the Gemini API key

In `mcp-client-python`, create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Do not commit `.env` or share your API key publicly.

### 2. Install and run

Open a terminal in `mcp-client-python` and run:

```bash
uv sync
uv run client.py uv --directory ../github-server run github_server.py
```

The client starts the GitHub MCP server over standard input/output (stdio), discovers its tools, and starts the interactive chat.

## Example questions

- What does `owner/repository` do?
- Show me the files in the `src` directory.
- Read the README of `owner/repository`.
- List the open issues in `owner/repository`.
- Summarise the latest pull requests.
- Show the most recent commits.

Replace `owner` and `repository` with a public GitHub repository's owner and name.

## Current scope and limitations

- The current tools are designed for **public GitHub repositories**.
- The server exposes read-only operations; it does not create issues, merge pull requests, push commits or modify repositories.
- Integration testing with Gemini and the complete local setup is still pending. Behaviour may vary with API availability, model configuration and repository rate limits.

## Attribution

DevPilot AI is adapted from the Python MCP client and server examples in the [Model Context Protocol Quickstart Resources](https://github.com/modelcontextprotocol/quickstart-resources). The GitHub-specific tools and Gemini integration are project modifications. Please retain and follow the original repository's license and attribution requirements.
