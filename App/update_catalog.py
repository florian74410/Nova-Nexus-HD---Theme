"""Offline version chooser for Updates/index.json. No unattended execution."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "Updates"
VERSION = re.compile(r"^v?[0-9]+(?:\.[0-9]+){2}(?:[-.][a-zA-Z0-9.-]+)?$")

def versions(root=None):
    root = Path(root) if root else ROOT
    try:
        data = json.loads((root / "index.json").read_text(encoding="utf-8"))
        entries = data.get("versions", [])
        if not isinstance(entries, list):
            return []
        accepted = []
        for item in entries:
            if not isinstance(item, dict) or not VERSION.fullmatch(str(item.get("version", ""))):
                continue
            filename = item.get("file")
            checksum = item.get("sha256")
            if not isinstance(filename, str) or Path(filename).name != filename or filename.startswith("."):
                continue
            if not isinstance(checksum, str) or not re.fullmatch(r"[a-fA-F0-9]{64}", checksum):
                continue
            accepted.append({"version": item["version"], "file": filename, "sha256": checksum.lower(),
                             "channel": item.get("channel", "stable")})
        return accepted
    except (OSError, ValueError, TypeError):
        return []
