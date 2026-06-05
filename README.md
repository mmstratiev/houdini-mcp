# HoudiniMCP – Connect Houdini to an AI via Model Context Protocol

**HoudiniMCP** allows you to control **SideFX Houdini** from an AI assistant using the **Model Context Protocol (MCP)**. It consists of:

1. A **Houdini plugin** that listens on `localhost:9876` and handles commands (creating nodes, executing code, rendering, etc.).
2. An **MCP bridge script** (`houdini_mcp_server.py`) that communicates over stdio with the AI client and over TCP with Houdini.

---

## Requirements

- **SideFX Houdini**
- **Python 3.x** (to run the install script)
- An **MCP-compatible AI client** (Claude Desktop, Cursor, etc.)

---

## Automatic Installation

Run the install script from the repo root:

```
python install.py
```

This will:
- Detect your Houdini version (prompts if multiple are found)
- Copy all plugin files to `~/Documents/houdiniXX.X/scripts/python/houdinimcp/`
- Install Python dependencies via `uv` (installs `uv` automatically if not found)
- Create `packages/houdinimcp.json` so Houdini loads the plugin at startup
- Create the **HoudiniMCP** shelf tool with a Toggle MCP Server button

After running, restart Houdini and [configure your MCP client](#configuring-your-mcp-client).

To uninstall:
```
python uninstall.py
```

---

## Manual Installation

### 1. Plugin Files

Create the plugin folder:
```
C:/Users/<YourUserName>/Documents/houdini21.0/scripts/python/houdinimcp/
```

Copy these files from the repo into it:

- **`__init__.py`** – handles plugin initialization (start/stop server)
- **`server.py`** – defines the `HoudiniMCPServer` (listening on port `9876`)
- **`houdini_mcp_server.py`** – MCP bridge script
- **`HoudiniMCPRender.py`** – handles render operations and output
- **`pyproject.toml`**
- **`uv.lock`**
- **`.python-version`**
- **`.env`** – copy `.env.example` and fill in your API key

### 2. Install Dependencies

Install [uv](https://docs.astral.sh/uv/) if you don't have it:
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install dependencies from the plugin directory:
```
cd C:/Users/<YourUserName>/Documents/houdini21.0/scripts/python/houdinimcp/
uv sync
```

### 3. Houdini Package

Create `C:/Users/<YourUserName>/Documents/houdini21.0/packages/houdinimcp.json`:

```json
{
  "path": "$HOME/houdini21.0/scripts/python",
  "load_package_once": true,
  "version": "0.1",
  "env": [
    {
      "PYTHONPATH": "$PYTHONPATH;$HOME/houdini21.0/scripts/python"
    }
  ]
}
```

### 4. Shelf Tool

1. **Right-click** the shelf bar → **New Shelf** → name it `HoudiniMCP`
2. **Right-click** the new shelf → **New Tool** → Name: `Toggle MCP Server`
3. Under **Script**, paste:

```python
import hou
import houdinimcp

if hasattr(hou.session, "houdinimcp_server") and hou.session.houdinimcp_server:
    houdinimcp.stop_server()
    hou.ui.displayMessage("Houdini MCP Server stopped")
else:
    houdinimcp.start_server()
    hou.ui.displayMessage("Houdini MCP Server started on localhost:9876")
```

---

## Configuring Your MCP Client

### Claude Desktop

Go to **File > Settings > Developer > Edit Config** and open `claude_desktop_config.json`. Add:

```json
{
  "mcpServers": {
    "houdini": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "C:/Users/<YourUserName>/Documents/houdini21.0/scripts/python/houdinimcp",
        "python",
        "C:/Users/<YourUserName>/Documents/houdini21.0/scripts/python/houdinimcp/houdini_mcp_server.py"
      ]
    }
  }
}
```

The `--project` flag tells uv where to find the `.python-version` and `uv.lock` files, ensuring the correct Python version and dependencies are used.

### Cursor

Go to **Settings > MCP > Add new MCP server** and add the same entry as above.

---

## First Use

1. **Open Houdini** — the plugin loads automatically via the package file
2. **Add the shelf tab** — click **+** at the end of the shelf bar → **Shelves** → select **Houdini MCP** (one-time setup)
3. **Start the server** — click **Toggle MCP Server**; a dialog confirms it's running on `localhost:9876`
4. **Open Claude Desktop** — go to the MCP tools panel and confirm the `houdini` server is connected. Claude will have access to tools for getting scene info, creating and modifying nodes, executing Python in Houdini, and rendering. If you set up OPUS, it can also generate and import 3D assets.
5. **Stop the server** — click **Toggle MCP Server** again when done

### Example Prompts

```
What's in my current Houdini scene?
```
```
Create a grid SOP inside a new geo node and apply a mountain SOP to it
```
```
Write and run a Python script in Houdini that creates 10 scattered spheres with random sizes
```
```
Render a quad view of the scene and show me the result
```
```
Create an OPUS sofa with a red color and import it into the scene
```

---

## OPUS Integration

OPUS provides a large set of procedural furniture and environmental assets.

1. Create an account at [RapidAPI](https://rapidapi.com/)
2. Subscribe at [OPUS API](https://rapidapi.com/genel-gi78OM1rB/api/opus5/pricing)
3. Copy `.env.example` to `.env` in the plugin folder and set `RAPIDAPI_KEY` to your key

---

## Acknowledgement

HoudiniMCP was built following [blender-mcp](https://github.com/ahujasid/blender-mcp). We thank them for the contribution.
