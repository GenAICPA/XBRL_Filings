nstructions for Use
1. Prerequisites:

You need Python 3.10 or higher installed.
2. Setup:

The complete code for the server is in the file xbrl_mcp_server.py. Make sure you have this file.
Open your terminal or command prompt and install the necessary dependencies by running:
pip install "mcp[cli]" httpx
3. Running the Server:

To run the server, execute the script from your terminal:
python3 xbrl_mcp_server.py
The server will then start and listen for requests from an MCP client. It runs over standard input/output (stdio), so you won't see any server output in the terminal unless there's an error.
4. Connecting to an MCP Client (Example):

To use the server, you need to configure an MCP client to connect to it. For example, if you were using Claude for Desktop, you would edit its configuration file (claude_desktop_config.json) to tell it how to run the server.
You would add an entry like this, making sure to use the absolute path to the script:
{
  "mcpServers": {
    "xbrl_filings": {
      "command": "python3",
      "args": [
        "/path/to/your/project/xbrl_mcp_server.py"
      ]
    }
  }
}
Once the client is configured and restarted, it will be able to see and use the get_filings tool provided by the server.
