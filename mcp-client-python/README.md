# DevPilot AI — MCP Client

The DevPilot AI client is an interactive Python application that connects to an MCP server over stdio, discovers its available tools, and makes them available to Google Gemini.

The included GitHub MCP server provides read-only tools for exploring public GitHub repositories.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- A Google Gemini API key

## Setup

Create a `.env` file in this directory:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Keep this file private. Do not commit it to GitHub.

Install the client dependencies:

```bash
uv sync
```

## Run with the DevPilot GitHub server

From this directory, run:

```bash
uv run client.py uv --directory ../github-server run github_server.py
```

The client launches the server as a subprocess, connects over stdio, discovers its tools, and starts the interactive chat.

## Use

Ask natural-language questions about a public GitHub repository, for example:

- `What does owner/repository do?`
- `List the files in owner/repository.`
- `Read the README.md file.`
- `Show open issues.`
- `Summarise recent pull requests.`
- `Show the latest commits.`

Replace `owner` and `repository` with the repository owner's GitHub username or organisation and repository name.

Type `quit` to exit. The current client implementation handles each query independently; persistent multi-turn conversation history is not yet implemented.

## Troubleshooting

- If the client reports that `GEMINI_API_KEY` is missing, check that `.env` exists in this directory and contains the key.
- If the MCP server cannot start, confirm that `github-server/github_server.py` exists and that `uv` is installed.
- If GitHub returns an error, check the repository owner/name, network connection and GitHub API rate limits.

## Attribution

This client is adapted from the Python MCP client example in the [Model Context Protocol Quickstart Resources](https://github.com/modelcontextprotocol/quickstart-resources), with project modifications for DevPilot AI and Google Gemini. Retain and follow the original source repository's license and attribution requirements.
