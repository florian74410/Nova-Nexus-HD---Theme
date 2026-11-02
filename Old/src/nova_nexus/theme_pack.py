"""NOVA NEXUS HD user-space theme pack integration.

Install an opt-in launcher's desktop entry, export theme assets and keep existing
NovaBar bars/docks untouched. Never changes defaults, polkit or login managers.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import shutil
import sys

from .desktop_theme import export_gtk_theme
from .xfwm4 import export_xfwm4_theme

NAME = "NOVA NEXUS HD"
DESKTOP_FILENAME = "nova-nexus-explorer.desktop"


def desktop_entry(python: str, root: Path, *, frozen: bool = False) -> str:
    # Desktop-entry Exec command quoting: paths cannot contain embedded quotes or newlines.
    for value in (python, str(root)):
        if any(ch in value for ch in ('"', "\n", "\r", "\0")):
            raise ValueError("Unsupported executable or project path")
    from healthbar.autostart import desktop_quote
    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=NOVA Explorer\n"
        "Comment=NOVA NEXUS HD experimental file manager\n"
        f'Exec={desktop_quote(python)} {"--nova-explorer" if frozen else "-m nova_nexus.explorer"} %f\n'
        f'Path={root}\n'
        "Terminal=false\n"
        "Categories=System;FileManager;\n"
        "StartupNotify=true\n"
        "MimeType=inode/directory;\n"
        "Icon=system-file-manager\n"
        "NoDisplay=false\n"
    )


def terminal_entry(python: str, root: Path, *, frozen: bool = False) -> str:
    entry=desktop_entry(python,root,frozen=frozen)
    return entry.replace("Name=NOVA Explorer","Name=NOVA Terminal").replace(
        "Comment=NOVA NEXUS HD experimental file manager","Comment=NOVA NEXUS HD interactive Linux terminal").replace(
        "--nova-explorer" if frozen else "-m nova_nexus.explorer",
        "--nova-terminal" if frozen else "-m nova_nexus.terminal").replace(
        " %f", "").replace("System;FileManager;","System;TerminalEmulator;").replace(
        "Icon=system-file-manager","Icon=utilities-terminal").replace(
        "MimeType=inode/directory;\n","")+"X-NOVA-Owned=true\nOnlyShowIn=XFCE;\n"


def install_user_pack(*, python: str | None = None, root: Path | None = None, frozen: bool = False) -> dict[str, str]:
    root = (root or Path(__file__).resolve().parent.parent).resolve()
    python = python or sys.executable
    applications = Path.home() / ".local/share/applications"
    applications.mkdir(parents=True, exist_ok=True)
    desktop = applications / DESKTOP_FILENAME
    # No overwriting arbitrary third-party custom launchers.
    if desktop.exists() and "NOVA NEXUS HD experimental file manager" not in desktop.read_text(encoding="utf-8"):
        raise FileExistsError(f"Refusing to overwrite foreign launcher: {desktop}")
    # Install only an opt-in app launcher. Do not modify xdg-mime default handler.
    desktop.write_text(desktop_entry(python, root, frozen=frozen), encoding="utf-8")
    theme = Path.home() / ".local/share/themes/NOVA-NEXUS-HD"
    export_gtk_theme(theme)
    export_xfwm4_theme(theme)
    wallpaper_src = Path(__file__).resolve().parent / "assets/nova-electric-blue-pcb.svg"
    wallpaper_dst = Path.home() / ".local/share/backgrounds/nova-electric-blue-pcb.svg"
    if wallpaper_src.is_file():
        wallpaper_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(wallpaper_src, wallpaper_dst)
    terminal=applications/"nova-nexus-terminal.desktop"
    if terminal.exists() and "X-NOVA-Owned=true" not in terminal.read_text(encoding="utf-8"):
        raise FileExistsError(f"Refusing to overwrite foreign launcher: {terminal}")
    terminal.write_text(terminal_entry(python, root, frozen=frozen),encoding="utf-8")
    return {"terminal": str(terminal), "desktop": str(desktop), "theme": str(theme), "wallpaper": str(wallpaper_dst)}


def uninstall_user_pack() -> None:
    desktop = Path.home() / ".local/share/applications" / DESKTOP_FILENAME
    if desktop.exists() and "NOVA NEXUS HD experimental file manager" in desktop.read_text(encoding="utf-8"):
        desktop.unlink()
    terminal=Path.home()/".local/share/applications/nova-nexus-terminal.desktop"
    if terminal.exists() and "X-NOVA-Owned=true" in terminal.read_text(encoding="utf-8"):
        terminal.unlink()
    # Keep themes/wallpapers because the user could have selected or customized them.


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="NOVA NEXUS HD preview pack")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", action="store_true")
    group.add_argument("--remove-launcher", action="store_true")
    group.add_argument("--preview-notification", action="store_true")
    args = parser.parse_args(argv)
    if args.install:
        for key, value in install_user_pack().items():
            print(f"{key}: {value}")
        print("Existing NovaBar bars, docks, profiles and XFCE notifications unchanged.")
    elif args.remove_launcher:
        uninstall_user_pack()
        print("NOVA Explorer launcher removed; existing theme files preserved.")
    else:
        from PySide6.QtWidgets import QApplication
        from .widgets import make_notification
        app = QApplication.instance() or QApplication(sys.argv)
        toast = make_notification("NOVA / NOTIFICATION", "NOVA NEXUS HD — aperçu du pack",
                                  actions=[("FERMER", lambda: toast.close())])
        toast.show()
        app.exec()


if __name__ == "__main__":
    main()
