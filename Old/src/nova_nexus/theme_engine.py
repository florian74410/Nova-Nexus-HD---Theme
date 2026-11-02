"""NOVA NEXUS HD — versioned, user-configurable theme tokens.

Pure Python: can be consumed by Qt components without modifying XFCE settings.
No system changes are performed on import or load.
"""
from __future__ import annotations

import json
import math
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULT_THEME: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "name": "Electric Blue PCB",
    "colors": {
        "background": "#09111B",
        "surface": "#111F2C",
        "surface_raised": "#172A39",
        "primary": "#00CBF3",
        "secondary": "#277FEA",
        "text": "#F2F8FF",
        "text_muted": "#A6BFCD",
        "success": "#32E0AF",
        "warning": "#FFB347",
        "danger": "#FF526A",
    },
    "effects": {
        "glass_opacity": 0.96,
        "reflection_intensity": 0.5,
        "font_scale": 1.0,
        "animation_speed": 1.0,
        "glow": 0.55,
        "shadow": 0.65,
        "opacity": 0.96,
        "pcb_visibility": 0.32,
        "border_width": 1.5,
        "bevel_size": 9,
    },
    "motion": {"enabled": True, "duration_ms": 190, "reduce_motion": False},
    "notifications": {"duration_ms": 5000, "position": "top-right"},
    "explorer": {"icon_size": 44, "animated_navigation": True},
}
_ALLOWED = {
    "colors": set(DEFAULT_THEME["colors"]),
    "effects": set(DEFAULT_THEME["effects"]),
    "motion": set(DEFAULT_THEME["motion"]),
    "notifications": set(DEFAULT_THEME["notifications"]),
    "explorer": set(DEFAULT_THEME["explorer"]),
}
_OPTIONAL_EFFECTS = {"glass_opacity", "reflection_intensity", "font_scale", "animation_speed"}
_RANGES = {
    "glass_opacity": (0.4, 1.0), "reflection_intensity": (0, 1),
    "font_scale": (0.75, 2.0), "animation_speed": (0.25, 3.0),
    "glow": (0.0, 1.0),
    "shadow": (0.0, 1.0),
    "opacity": (0.4, 1.0),
    "pcb_visibility": (0.0, 1.0),
    "border_width": (0.5, 5.0),
    "bevel_size": (0, 30),
    "duration_ms": (0, 1200),
    "icon_size": (16, 128),
}
_POSITIONS = {"top-left", "top-right", "bottom-left", "bottom-right"}


class ThemeError(ValueError):
    """Invalid or incompatible NOVA theme."""


def validate_theme(candidate: Any) -> dict[str, Any]:
    """Validate a full theme, reject unknown tokens, and normalize safe values."""
    if not isinstance(candidate, dict):
        raise ThemeError("Theme must be a JSON object")
    if set(candidate) != {"schema_version", "name", *_ALLOWED}:
        raise ThemeError("Missing or unexpected top-level theme keys")
    if type(candidate["schema_version"]) is not int or candidate["schema_version"] != SCHEMA_VERSION:
        raise ThemeError("Unsupported theme schema")
    if not isinstance(candidate["name"], str) or not (1 <= len(candidate["name"]) <= 64):
        raise ThemeError("Invalid theme name")
    theme = deepcopy(candidate)
    for section, allowed in _ALLOWED.items():
        values = theme[section]
        if section == "effects" and isinstance(values,dict) and set(values)<=allowed and allowed-set(values)<=_OPTIONAL_EFFECTS:
            values = theme[section] = {**DEFAULT_THEME[section], **values}
        if not isinstance(values, dict) or set(values) != allowed:
            raise ThemeError("Invalid theme section: " + section)
        for key, value in values.items():
            if section == "colors":
                if not isinstance(value, str) or not HEX_COLOR.fullmatch(value):
                    raise ThemeError("Invalid color: " + key)
                values[key] = value.upper()
            elif key in ("enabled", "reduce_motion", "animated_navigation"):
                if type(value) is not bool:
                    raise ThemeError("Expected boolean: " + key)
            elif key == "position":
                if value not in _POSITIONS:
                    raise ThemeError("Invalid notification position")
            else:
                lo, hi = (1000, 30000) if section == "notifications" and key == "duration_ms" else _RANGES[key]
                if type(value) not in (int, float) or not math.isfinite(value) or not lo <= value <= hi:
                    raise ThemeError("Value out of range: " + key)
    return theme


def load_theme(path: str | Path) -> dict[str, Any]:
    """Read UTF-8 JSON theme; never execute config contents."""
    if Path(path).stat().st_size > 64 * 1024:
        raise ThemeError("Theme exceeds 64 KiB")
    with Path(path).open("r", encoding="utf-8") as handle:
        return validate_theme(json.load(handle))


def save_theme(path: str | Path, theme: dict[str, Any]) -> None:
    """Atomically save a validated theme; does not change XFCE settings."""
    import os
    import tempfile
    target = Path(path)
    validated = validate_theme(theme)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".nova-theme-", suffix=".tmp", dir=target.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            json.dump(validated, out, ensure_ascii=False, indent=2)
            out.write("\n")
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def get_default_theme() -> dict[str, Any]:
    return deepcopy(DEFAULT_THEME)


def qt_stylesheet(theme: dict[str, Any]) -> str:
    """Baseline Qt styling. Custom polygonal frames/PCB routes need paintEvent."""
    t = validate_theme(theme)
    c, e = t["colors"], t["effects"]
    return (
        "QWidget { background-color: " + c["background"] + "; color: " + c["text"] + "; }\n"
        "QDialog, QMenu { background-color: " + c["surface"] + "; "
        "border: " + str(e["border_width"]) + "px solid " + c["secondary"] + "; }\n"
        "QPushButton { background-color: " + c["surface_raised"] + "; "
        "color: " + c["text"] + "; border: 1px solid " + c["primary"] + "; "
        "padding: 8px 14px; border-radius: 0px; }\n"
        "QPushButton:hover { background-color: " + c["secondary"] + "; }\n"
        "QLineEdit { color: " + c["text"] + "; background: " + c["surface"] + "; "
        "border: 1px solid " + c["secondary"] + "; padding: 6px; }\n"
    )

PALETTES = {
    'Electric Blue': ('#00CBF3', '#277FEA'),
    'Matrix Green': ('#40F58A', '#168B4D'),
    'Cyber Magenta': ('#F34DEB', '#9136C4'),
    'Tactical Amber': ('#FFBD45', '#B97816'),
    'Stealth Dark': ('#9CAFC1', '#526477'),
}


def preset(name='Electric Blue', mode='Standard'):
    if name not in PALETTES or mode not in ('Off', 'Eco', 'Standard', 'Ultra'):
        raise ThemeError('Unknown palette or effects mode')
    theme = get_default_theme()
    theme['name'] = name
    theme['colors']['primary'], theme['colors']['secondary'] = PALETTES[name]
    glow, pcb, motion = {'Off': (0, 0, False), 'Eco': (.25, .15, False),
                         'Standard': (.55, .32, True), 'Ultra': (.85, .6, True)}[mode]
    theme['effects'].update(glow=glow, pcb_visibility=pcb)
    theme['motion']['enabled'] = motion
    return theme


def active_theme_path():
    from healthbar.config import data_dir
    return data_dir() / 'nova-theme.json'


def get_active_theme():
    path = active_theme_path()
    if path.exists():
        return load_theme(path)
    return get_default_theme()


def set_active_theme(theme):
    save_theme(active_theme_path(), theme)
