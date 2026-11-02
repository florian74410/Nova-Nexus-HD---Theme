"""NOVA wallpaper utility: opt-in current XFCE desktop background.

No root access. Only changes desktop backdrop if --apply is supplied.
"""
from __future__ import annotations
import argparse
import json
import shutil
import subprocess
from pathlib import Path

WALLPAPER = Path(__file__).resolve().parent / "assets/nova-electric-blue-pcb.svg"
STATE = Path.home() / ".config/nova-nexus/wallpaper-backup.json"


def xfconf(command, *args):
    return subprocess.check_output(["xfconf-query", "-c", "xfce4-desktop", *command, *args], text=True).strip()


def background_properties():
    output = xfconf(["-l"])
    return [line for line in output.splitlines()
            if line.endswith("/last-image") or line.endswith("/image-path")]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--restore", action="store_true")
    args = parser.parse_args()
    if args.restore:
        if not STATE.exists():
            parser.error("No saved desktop wallpaper state")
        settings = json.loads(STATE.read_text(encoding="utf-8"))
        for prop, value in settings.items():
            subprocess.run(["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", value], check=True)
        print("Previous wallpaper restored.")
        return
    if not WALLPAPER.exists():
        parser.error("Wallpaper asset missing: " + str(WALLPAPER))
    target = Path.home() / ".local/share/backgrounds/nova-electric-blue-pcb.svg"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(WALLPAPER, target)
    print("NOVA wallpaper copied to", target)
    if not args.apply:
        print("Not activated. Run with --apply to set wallpaper for discovered XFCE backdrops.")
        return
    props = background_properties()
    if not props:
        parser.error("No XFCE background properties detected")
    previous = {prop: xfconf(["-p", prop]) for prop in props}
    STATE.parent.mkdir(parents=True, exist_ok=True)
    if not STATE.exists():
        STATE.write_text(json.dumps(previous, indent=2) + "\n", encoding="utf-8")
    for prop in props:
        subprocess.run(["xfconf-query", "-c", "xfce4-desktop", "-p", prop, "-s", str(target)], check=True)
    print("Applied NOVA wallpaper; restore with --restore.")


if __name__ == "__main__":
    main()
