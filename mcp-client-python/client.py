
import asyncio
import os
import sys
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from google import genai
from google.genai import types
from mcp import Client, MCPError, StdioServerParameters
from mcp_types import (
    EmbeddedResource,
    TextContent,
    TextResourceContents,
)

load_dotenv()

GEMINI_MODEL = "gemini-3.8-flash"
MAX_TOOL_TURNS = 10

SYSTEM_PROMPT = """
You are DevPilot AI, a GitHub Repository Intelligence Assistant.

Help developers explore and understand GitHub repositories.
Use the available MCP tools when repository information is needed.
Explain results clearly and distinguish retrieved information from assumptions.
Only perform operations supported by the available tools.
"""


def get_tool_text(result) -> str:
    """Convert MCP results into text for Gemini."""
    output = []

    for block in result.content:
        if isinstance(block, TextContent):
            output.append(block.text)
        elif isinstance(block, EmbeddedResource):
            if isinstance(block.resource, TextResourceContents):
                output.append(block.resource.text)
            else:
                output.append("[Embedded resource returned]")
        else:
            output.append(f"[Unsupported content type: {block.type}]")

    if result.structured_content is not None and not output:
        output.append(str(result.structured_content))

    return "\n".join(output) or "Tool returned no text."


class MCPClient:
    def __init__(self):
        self.client: Client | None = None
        self.exit_stack = AsyncExitStack()
        self.gemini = None
        self.tools = []
        self.gemini_tools = []

    async def connect_to_server(self, server_command: list[str]):
        server_params = StdioServerParameters(
            command=server_command[0],
            args=server_command[1:],
        )

        self.client = await self.exit_stack.enter_async_context(
            Client(
                server_params,
                mode="auto",
            )
        )

        response = await self.client.list_tools()

        self.tools = response.tools

        declarations = [
            types.FunctionDeclaration(
                name=tool.name,
                description=tool.description or tool.name,
                parameters_json_schema=tool.input_schema,
            )
            for tool in self.tools
        ]

        self.gemini_tools = [
            types.Tool(function_declarations=declarations)
        ]

        print(
            f"\nConnected over protocol {self.client.protocol_version}"
        )
        print("Available GitHub tools:", [tool.name for tool in self.tools])

    def initialize_gemini(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in .env")

        self.gemini = genai.Client(api_key=api_key)

    async def process_query(self, query: str) -> str:
        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=query)],
            )
        ]

        final_text = []

        for turn in range(MAX_TOOL_TURNS + 1):
            response = self.gemini.models.generate_content(
                model=GEMINI_MODEL,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    tools=self.gemini_tools,
                    max_output_tokens=8192,
                ),
            )

            if not response.candidates:
                return "Gemini did not return a response."

            model_content = response.candidates[0].content
            function_calls = response.function_calls or []

            if not function_calls:
                contents.append(model_content)
                if response.text:
                    final_text.append(response.text)
                break

            contents.append(model_content)

            if turn == MAX_TOOL_TURNS:
                final_text.append(
                    f"Stopped after {MAX_TOOL_TURNS} tool-use turns."
                )
                break

            function_responses = []

            for call in function_calls:
                print(f"\n[Calling {call.name} with {call.args}]")

                try:
                    result = await self.client.call_tool(
                        call.name,
                        dict(call.args),
                    )
                    tool_output = get_tool_text(result)

                    if result.is_error:
                        function_response = {"error": tool_output}
                    else:
                        function_response = {"result": tool_output}

                except MCPError as error:
                    function_response = {"error": str(error)}

                final_text.append(
                    f"[Tool {call.name} executed]"
                )

                function_responses.append(
                    types.Part.from_function_response(
                        name=call.name,
                        response=function_response,
                    )
                )

            contents.append(
                types.Content(
                    role="tool",
                    parts=function_responses,
                )
            )

        return "\n".join(final_text)

    async def chat_loop(self):
        print("\nDevPilot AI Started!")
        print("Ask questions about GitHub repositories.")
        print("Type 'clear' to reset or 'quit' to exit.")

        while True:
            try:
                query = (
                    await asyncio.to_thread(input, "\nDevPilot > ")
                ).strip()
            except (EOFError, KeyboardInterrupt):
                break

            if query.lower() == "quit":
                break

            if query.lower() == "clear":
                print("Conversation reset.")
                continue

            if not query:
                continue

            try:
                response = await self.process_query(query)
                print("\n" + response)
            except Exception as error:
                print(f"\nError: {error}")

    async def cleanup(self):
        await self.exit_stack.aclose()
        if self.gemini:
            self.gemini.close()


async def main():
    if len(sys.argv) < 2:
        print(
            "Usage: uv run client.py <server_command> [args...]",
            file=sys.stderr,
        )
        sys.exit(1)

    client = MCPClient()

    try:
        await client.connect_to_server(sys.argv[1:])
        client.initialize_gemini()
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
