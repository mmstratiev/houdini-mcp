#!/usr/bin/env python
"""
uninstall.py

Removes HoudiniMCP from the Houdini user directory:
  - Deletes scripts/python/houdinimcp/
  - Deletes packages/houdinimcp.json
  - Deletes toolbar/houdinimcp.shelf
"""
import pathlib
import shutil
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


def find_houdini_user_dirs():
    docs = pathlib.Path.home() / "Documents"
    return sorted(docs.glob("houdini*.*"), reverse=True)


def main():
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

    targets = [
        houdini_dir / "scripts" / "python" / "houdinimcp",
        houdini_dir / "packages" / "houdinimcp.json",
        houdini_dir / "toolbar" / "houdinimcp.shelf",
    ]

    print("\nThe following will be removed:")
    for t in targets:
        status = "found" if t.exists() else "not found"
        print(f"  {t}  [{status}]")

    answer = input("\nProceed? [y/N]: ").strip().lower()
    if answer != "y":
        print("Aborted.")
        return

    for t in targets:
        if not t.exists():
            print(f"Skipped (not found): {t.name}")
            continue
        if t.is_dir():
            shutil.rmtree(t)
        else:
            t.unlink()
        print(f"Removed: {t}")

    print("\nDone. Restart Houdini to apply changes.")


if __name__ == "__main__":
    main()
