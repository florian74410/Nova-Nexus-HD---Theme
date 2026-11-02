"""Read-only plugin manifests, deliberately does NOT import or execute plugin code."""
from __future__ import annotations
import json
import re
from pathlib import Path

ID = re.compile(r"^[a-z][a-z0-9_-]{1,39}$")
SUPPORTED = {"boolean", "integer", "text"}
ROOT = Path(__file__).resolve().parents[1] / "Plugins"

def discover(root=None):
    source = Path(root) if root else ROOT
    result = []
    if not source.is_dir():
        return result
    for path in sorted(source.glob("*/manifest.json")):
        if path.is_symlink() or path.parent.is_symlink():
            continue
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
            ident = manifest["id"]
            if not ID.fullmatch(ident) or ident != path.parent.name:
                continue
            if not isinstance(manifest["name"], str) or not isinstance(manifest["version"], str):
                continue
            settings = manifest.get("settings", [])
            if not isinstance(settings, list) or len(settings) > 30:
                continue
            if any(not isinstance(s, dict) or not ID.fullmatch(str(s.get("key", "")))
                   or s.get("type") not in SUPPORTED for s in settings):
                continue
            result.append({"id": ident, "name": manifest["name"][:70],
                           "version": manifest["version"][:32], "settings": settings})
        except (OSError, ValueError, TypeError, KeyError):
            continue
    return result
