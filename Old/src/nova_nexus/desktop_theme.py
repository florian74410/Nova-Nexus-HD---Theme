"""Safe opt-in desktop theme exporter for XFCE GTK and XFWM4.

Exports ordinary user-owned theme files. Does NOT activate, touch /etc,
change a login/lock screen or replace a desktop daemon.
"""
from __future__ import annotations
import html
from pathlib import Path
from .theme_engine import get_default_theme, validate_theme


def render_gtk_css(theme=None):
    t = validate_theme(theme or get_default_theme())
    c = t["colors"]
    base = """
/* NOVA NEXUS HD GTK3 overlay — only GTK widgets honoring user themes */
@define-color theme_bg_color %s;
@define-color theme_fg_color %s;
@define-color theme_selected_bg_color %s;
@define-color theme_selected_fg_color %s;
window, dialog, .background { background-color: %s; color: %s; }
button { border-radius: 0; border: 1px solid %s; background: %s; color: %s; }
button:hover { border-color: %s; background: %s; }
entry { border-radius: 0; border: 1px solid %s; background: %s; color: %s; }
menu, menuitem, popover { background: %s; color: %s; }
menuitem:hover { background: %s; }
""" % (c["background"], c["text"], c["secondary"], c["text"],
       c["background"], c["text"], c["primary"], c["surface_raised"], c["text"],
       c["primary"], c["secondary"], c["secondary"], c["surface"], c["text"],
       c["surface"], c["text"], c["surface_raised"])

    return base + """
headerbar, .titlebar { background: #253641; color: #F2F8FF; border-bottom: 1px solid #00CBF3; }
headerbar button.titlebutton, .titlebar button.titlebutton {
  background: #071C30; color: #FF526A; border: 1px solid #00CBF3;
  border-radius: 0; padding: 3px; min-width: 22px; min-height: 22px;
  -gtk-icon-shadow: none; box-shadow: none;
}
headerbar button.titlebutton:hover, .titlebar button.titlebutton:hover { background: #124E75; border-color: #3EEBFF; }
button.titlebutton image { color: #FF526A; -gtk-icon-style: symbolic; }
button.titlebutton.minimize image { -gtk-icon-source: url("assets/minimize.svg"); }
button.titlebutton.maximize image { -gtk-icon-source: url("assets/maximize.svg"); }
window.maximized button.titlebutton.maximize image { -gtk-icon-source: url("assets/restore.svg"); }
button.titlebutton.close image { -gtk-icon-source: url("assets/close.svg"); }
"""


def export_gtk_theme(destination, theme=None):
    """Export a standalone GTK theme skeleton to an explicit destination."""
    t = validate_theme(theme or get_default_theme())
    target = Path(destination).expanduser()
    directory = target / "gtk-3.0"
    directory.mkdir(parents=True, exist_ok=True)
    assets = directory / "assets"
    assets.mkdir(exist_ok=True)
    symbols = {"minimize": "M4 12H14", "maximize": "M4 4H14V14H4ZM4 7H14",
               "restore": "M7 7V4H14V11H11M4 7H11V14H4Z", "close": "M5 5L13 13M13 5L5 13"}
    for name, path in symbols.items():
        (assets / (name + ".svg")).write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18">'
            '<path d="' + path + '" fill="none" stroke="#FF526A" stroke-width="2"/></svg>\n',
            encoding="utf-8")
    (directory / "gtk.css").write_text(render_gtk_css(t), encoding="utf-8")
    (target / "index.theme").write_text(
        "[Desktop Entry]\nType=X-GNOME-Metatheme\nName=NOVA NEXUS HD\n"
        "Comment=Experimental NOVA theme\n", encoding="utf-8")
    return target
