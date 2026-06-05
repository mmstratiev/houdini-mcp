#!/usr/bin/env python
"""
install.py

Run once from the repo root to set up HoudiniMCP:
  - Copies plugin files to ~/Documents/houdiniXX.X/scripts/python/houdinimcp/
  - Creates the Houdini package JSON in ~/Documents/houdiniXX.X/packages/
  - Creates the MCP shelf tool in ~/Documents/houdiniXX.X/toolbar/
"""
import json
import os
import pathlib
import glob
import shutil
import subprocess
import sys


def pick(options):
    """Arrow-key selection, stdlib only. Returns the selected index."""
    selected = 0
    first = True

    def render():
        nonlocal first
        if not first:
            sys.stdout.write(f"\033[{len(options)}A")
        first = False
        for i, opt in enumerate(options):
            prefix = "> " if i == selected else "  "
            sys.stdout.write(f"\r{prefix}{opt}\033[K\n")
        sys.stdout.flush()

    render()

    if sys.platform == "win32":
        import msvcrt
        while True:
            key = msvcrt.getch()
            if key == b'\xe0':
                key = msvcrt.getch()
                if key == b'H':
                    selected = (selected - 1) % len(options)
                elif key == b'P':
                    selected = (selected + 1) % len(options)
            elif key in (b'\r', b'\n'):
                return selected
            render()
    else:
        import tty
        import termios
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch == '\x1b':
                    ch2 = sys.stdin.read(2)
                    if ch2 == '[A':
                        selected = (selected - 1) % len(options)
                    elif ch2 == '[B':
                        selected = (selected + 1) % len(options)
                elif ch in ('\r', '\n'):
                    return selected
                render()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

PLUGIN_FILES = [
    "__init__.py",
    "server.py",
    "houdini_mcp_server.py",
    "HoudiniMCPRender.py",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
]

SHELF_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<shelfDocument>
  <toolshelf name="houdinimcp" label="Houdini MCP">
    <memberTool name="toggle_mcp_server"/>
  </toolshelf>
  <tool name="toggle_mcp_server" label="Toggle MCP Server" icon="MISC_server">
    <script scriptType="python"><![CDATA[
import hou
import houdinimcp

if hasattr(hou.session, "houdinimcp_server") and hou.session.houdinimcp_server:
    houdinimcp.stop_server()
    hou.ui.displayMessage("Houdini MCP Server stopped")
else:
    houdinimcp.start_server()
    hou.ui.displayMessage("Houdini MCP Server started on localhost:9876")
]]></script>
  </tool>
</shelfDocument>
"""


def ensure_uv() -> str:
    """Return path to uv, installing it if necessary. Returns None if install declined."""
    uv = shutil.which("uv")
    if uv:
        return uv

    # Check the default install location in case PATH isn't updated yet
    default = pathlib.Path.home() / ".local" / "bin" / ("uv.exe" if sys.platform == "win32" else "uv")
    if default.exists():
        return str(default)

    print("uv is not installed.")
    answer = input("Install uv now? [Y/n]: ").strip().lower() or "y"
    if answer != "y":
        print("Skipping uv install. Run 'uv sync' manually in the plugin directory.")
        return None

    if sys.platform == "win32":
        cmd = ["powershell", "-c", "irm https://astral.sh/uv/install.ps1 | iex"]
    else:
        cmd = ["sh", "-c", "curl -LsSf https://astral.sh/uv/install.sh | sh"]

    print("Installing uv...")
    subprocess.run(cmd, check=True)
    return str(default) if default.exists() else shutil.which("uv")


def find_houdini_user_dirs():
    docs = pathlib.Path.home() / "Documents"
    return sorted(docs.glob("houdini*.*"), reverse=True)


def main():
    plugin_dir = pathlib.Path(__file__).parent.resolve()

    dirs = find_houdini_user_dirs()
    if not dirs:
        print("No Houdini user directories found in ~/Documents.")
        return

    if len(dirs) == 1:
        houdini_dir = dirs[0]
        print(f"Found: {houdini_dir}")
    else:
        print("Select Houdini version (arrow keys + Enter):")
        houdini_dir = dirs[pick([d.name for d in dirs])]

    # --- Copy plugin files ---
    dest = houdini_dir / "scripts" / "python" / "houdinimcp"
    dest.mkdir(parents=True, exist_ok=True)

    for filename in PLUGIN_FILES:
        src = plugin_dir / filename
        if src.exists():
            shutil.copy2(src, dest / filename)
            print(f"Copied: {filename}")
        else:
            print(f"Warning: {filename} not found in repo, skipping.")

    env_dest = dest / ".env"
    if env_dest.exists():
        env_created = False
        print("Skipped: .env already exists")
    else:
        env_created = True
        shutil.copy2(plugin_dir / ".env.example", dest / ".env")
        print("Copied: .env.example → .env")

    # --- Install dependencies ---
    uv = ensure_uv()
    if uv:
        print("Running uv sync...")
        subprocess.run([uv, "sync"], cwd=dest, check=True)
        print("Dependencies installed.")

    # --- Package JSON ---
    packages_dir = houdini_dir / "packages"
    packages_dir.mkdir(exist_ok=True)
    package_path = packages_dir / "houdinimcp.json"

    package = {
        "path": str(dest.parent),
        "load_package_once": True,
        "version": "0.1",
        "env": [
            {"PYTHONPATH": "$PYTHONPATH;" + str(dest.parent)}
        ]
    }

    package_path.write_text(json.dumps(package, indent=2))
    print(f"Created package: {package_path}")

    # --- Shelf tool ---
    toolbar_dir = houdini_dir / "toolbar"
    toolbar_dir.mkdir(exist_ok=True)
    shelf_path = toolbar_dir / "houdinimcp.shelf"

    shelf_path.write_text(SHELF_XML, encoding="utf-8")
    print(f"Created shelf:   {shelf_path}")

    script_path = str(dest / "houdini_mcp_server.py").replace("\\", "/")
    dest_str = str(dest).replace("\\", "/")

    print("\nDone. Restart Houdini and the MCP shelf will appear.")
    if env_created:
        print("\n--- OPUS Setup ---")
        print(f"Open the .env file and set your RapidAPI key:\n")
        print(f"  {dest_str}/.env\n")
        print("  RAPIDAPI_KEY=your_rapidapi_key_here")
    print("\n--- MCP Client Setup ---")
    print("Add the following to your AI client's MCP config (e.g. claude_desktop_config.json):\n")
    print(f'''{{
  "mcpServers": {{
    "houdini": {{
      "command": "uv",
      "args": [
        "run",
        "--project",
        "{dest_str}",
        "python",
        "{script_path}"
      ]
    }}
  }}
}}''')


if __name__ == "__main__":
    main()
