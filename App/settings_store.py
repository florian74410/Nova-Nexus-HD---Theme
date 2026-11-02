"""Validated, atomic configuration; no dependency on the legacy app."""
from __future__ import annotations
import json
import os
from pathlib import Path

DEFAULT = {
    "general": {"animations": True, "start_minimized": False},
    "theme": {"primary": "#00C8FF", "secondary": "#FF365F",
              "background": "#080F1D", "opacity": 94, "pcb_effects": True},
    "plugins": {}
}

def settings_path() -> Path:
    base = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    return base / "nova-nexus-hd" / "settings.json"

def valid_hex(value):
    return isinstance(value, str) and len(value) == 7 and value.startswith("#") and all(
        char in "0123456789abcdefABCDEF" for char in value[1:])

def validate(raw):
    safe = json.loads(json.dumps(DEFAULT))
    if not isinstance(raw, dict):
        return safe
    general = raw.get("general")
    if isinstance(general, dict):
        for key in safe["general"]:
            if type(general.get(key)) is bool:
                safe["general"][key] = general[key]
    theme = raw.get("theme")
    if isinstance(theme, dict):
        for key in ("primary", "secondary", "background"):
            if valid_hex(theme.get(key)):
                safe["theme"][key] = theme[key].upper()
        if type(theme.get("opacity")) is int and 65 <= theme["opacity"] <= 100:
            safe["theme"]["opacity"] = theme["opacity"]
        if type(theme.get("pcb_effects")) is bool:
            safe["theme"]["pcb_effects"] = theme["pcb_effects"]
    plugins = raw.get("plugins")
    if isinstance(plugins, dict):
        for plugin_id, values in plugins.items():
            if isinstance(plugin_id, str) and plugin_id.replace("-", "").replace("_", "").isalnum() and isinstance(values, dict):
                safe["plugins"][plugin_id] = {key: value for key, value in values.items()
                    if isinstance(key, str) and len(key) <= 60 and type(value) in (bool, int, float, str)}
    return safe

def load(path=None):
    target = Path(path) if path else settings_path()
    try:
        return validate(json.loads(target.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return validate({})

def save(value, path=None):
    target = Path(path) if path else settings_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(validate(value), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(target)
