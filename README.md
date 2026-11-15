# DevPilot AI

**An MCP-powered GitHub Repository Intelligence Assistant**

DevPilot AI is an AI-powered GitHub Repository Intelligence Assistant built using the **Model Context Protocol (MCP)** and **Google Gemini**. It enables developers to explore public GitHub repositories, understand codebases, and inspect repository activity through natural-language conversations.

##  Features

DevPilot currently provides six read-only GitHub tools:

- **Repository Information** — Retrieve repository metadata, including description, programming language, stars, forks, and default branch.
- **List Repository Files** — Browse repository files and directory structures.
- **Read Repository Files** — Retrieve the contents of supported text files.
- **Repository Issues** — Explore repository issues and their details.
- **Pull Requests** — Inspect pull requests, branches, and their status.
- **Recent Commits** — Review recent commits, messages, and authors.

##  Architecture

```text
                   User
                    |
                    v
              Python MCP Client
                    |
             Google Gemini API
                    |
             Tool Call Requests
                    |
                    v
              MCP Communication
                (stdio)
                    |
                    v
              GitHub MCP Server
                    |
              GitHub REST API
                    |
                    v
          Public GitHub Repositories
```

The MCP client discovers the tools exposed by the GitHub server and makes them available to Gemini. Based on the user's natural-language request, Gemini can request the appropriate tool calls. The client executes these calls through the MCP connection and returns the results.

##  Project Structure

```text
devpilot/
├── mcp-client-python/
│   ├── client.py
│   ├── pyproject.toml
│   ├── .env.example
│   └── README.md
│
├── github-server/
│   ├── github_server.py
│   ├── pyproject.toml
│   └── README.md
│
├── .gitignore
├── LICENSE
└── README.md
```

##  Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/)
- Google Gemini API key

##  Setup and Installation

### 1. Clone the repository

```bash
git clone https://github.com/bhumisuri2819-collab/devpilot.git
cd devpilot
```

### 2. Configure the API key

Navigate to `mcp-client-python` and create a `.env` file using `.env.example` as a reference.

```env
GEMINI_API_KEY=your_gemini_api_key
```

**Important:** Never commit your `.env` file or expose your API key publicly.

### 3. Install dependencies

From the `mcp-client-python` directory:

```bash
uv sync
```

### 4. Run DevPilot

```bash
uv run client.py uv --directory ../github-server run github_server.py
```

The client launches the GitHub MCP server using standard input/output (stdio), discovers its available tools, and starts the interactive chat.

##  Example Queries

Try asking DevPilot:

- What does `owner/repository` do?
- Show me the files in the `src` directory.
- Read the README of `owner/repository`.
- List the open issues in `owner/repository`.
- Summarise the latest pull requests.
- Show the most recent commits.

Replace `owner` and `repository` with the owner and name of a public GitHub repository.

##  Current Scope and Limitations

- Currently designed to work with **public GitHub repositories**.
- All exposed GitHub tools are read-only.
- Does not create issues, merge pull requests, push commits, or modify repositories.
- Full end-to-end integration testing with Gemini is still pending.

Behaviour may depend on API availability, model configuration, and GitHub API rate limits.

##  Future Improvements

- Persistent multi-turn conversation history.
- Advanced code search and repository exploration.
- Contributor insights and repository analytics.
- Expanded repository intelligence capabilities.

##  Attribution

DevPilot AI is adapted from the Python MCP client and server examples in the [Model Context Protocol Quickstart Resources](https://github.com/modelcontextprotocol/quickstart-resources).

The GitHub-specific tools and Gemini integration are project modifications. Original license and attribution requirements are retained.
