"""NOVA NEXUS HD — isolated v0.1 PySide6 settings popup."""
from __future__ import annotations
import copy
import math
import sys
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QCheckBox, QColorDialog, QSlider, QScrollArea,
    QComboBox, QMessageBox, QSpinBox, QLineEdit, QFrame)
from . import __version__
from .settings_store import DEFAULT, validate
from .plugin_registry import discover
from .update_catalog import versions
from .top_hud import TopHUD
from .telemetry import Telemetry

BASE_SECTIONS = ["Générale", "Thème Couleurs", "Plugins", "Mise à jour", "À Propos"]

class Circuits(QWidget):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.step = 0
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.advance)
        self.clock.start(65)

    def advance(self):
        if self.config["general"]["animations"] and self.config["theme"]["pcb_effects"]:
            self.step = (self.step + 1) % 600
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if w < 70 or h < 70:
            return
        theme = self.config["theme"]
        bg = QColor(theme["background"])
        bg.setAlphaF(theme["opacity"] / 100)
        outline = QColor(theme["primary"])
        outline.setAlpha(210)
        polygon = QPolygonF([QPointF(18, 0), QPointF(w-18, 0), QPointF(w, 18),
                    QPointF(w, h-18), QPointF(w-18, h), QPointF(18, h),
                    QPointF(0, h-18), QPointF(0, 18)])
        painter.setPen(QPen(outline, 1.6))
        painter.setBrush(bg)
        painter.drawPolygon(polygon)
        trace = QColor(theme["primary"])
        trace.setAlpha(65)
        dot = QColor(theme["secondary"])
        for index, y in enumerate(range(66, max(67, h-30), 72)):
            end = min(w-18, 92 + (index * 41) % 245)
            path = [QPointF(5, y), QPointF(21, y), QPointF(39, y+18),
                    QPointF(end-18, y+18), QPointF(end, y)]
            painter.setPen(QPen(trace, 1.25))
            for start, finish in zip(path, path[1:]):
                painter.drawLine(start, finish)
            painter.setPen(QPen(dot, 1))
            painter.setBrush(dot)
            painter.drawEllipse(path[-1], 2.4, 2.4)
            if self.config["general"]["animations"] and theme["pcb_effects"]:
                j = (self.step // 9 + index) % (len(path)-1)
                painter.setPen(QPen(QColor("#E5FDFF"), 2))
                painter.drawLine(path[j], path[j+1])
        painter.end()

class Settings(QWidget):
    def __init__(self):
        super().__init__()
        self.config = validate({})
        self.setWindowTitle("NOVA NEXUS HD — Paramètres")
        self.resize(1020, 665)
        self.setMinimumSize(820, 560)
        self.circuit = Circuits(self.config, self)
        self.circuit.lower()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 21, 25, 22)
        header = QHBoxLayout()
        brand = QLabel("◈   NOVA NEXUS HD")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        tag = QLabel("CONFIGURATION // v" + __version__)
        tag.setObjectName("dim")
        header.addWidget(tag)
        close = QPushButton("×")
        close.setObjectName("close")
        close.clicked.connect(self.close)
        header.addWidget(close)
        layout.addLayout(header)
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setObjectName("line")
        layout.addWidget(line)
        body = QHBoxLayout()
        body.setSpacing(20)
        sidebar = QWidget()
        sidebar.setFixedWidth(214)
        self.nav = QVBoxLayout(sidebar)
        self.nav.setContentsMargins(0, 16, 0, 0)
        self.nav.setSpacing(8)
        self.buttons = []
        self.plugin_rows = discover()
        self.stack = QStackedWidget()
        self.make_page("GÉNÉRALE", self.general_page)
        self.make_page("THÈME & COULEURS", self.theme_page)
        self.make_page("PLUGINS", self.plugins_page)
        self.make_page("MISE À JOUR", self.updates_page)
        self.make_page("À PROPOS", self.about_page)
        for title in BASE_SECTIONS:
            self.add_navigation(title)
        for plugin in self.plugin_rows:
            self.make_page(plugin["name"].upper(), lambda lay, p=plugin: self.plugin_page(lay, p))
            self.add_navigation("↳ " + plugin["name"])
        self.nav.addStretch()
        dim = QLabel("◉  LOCAL / SECURE")
        dim.setObjectName("dim")
        self.nav.addWidget(dim)
        body.addWidget(sidebar)
        body.addWidget(self.stack, 1)
        layout.addLayout(body, 1)
        self.apply_theme()
        self.hud = TopHUD(self.config)
        self.telemetry = Telemetry(parent=self)
        self.telemetry.sampled.connect(self.hud.set_sample)
        self.hud.cpu_gauge.details_requested.connect(self.cpu_details)
        self.sync_hud()
        self.show_page(0)

    def resizeEvent(self, event):
        self.circuit.setGeometry(self.rect())
        super().resizeEvent(event)

    def label(self, text):
        widget = QLabel(text)
        widget.setWordWrap(True)
        widget.setObjectName("description")
        return widget

    def make_page(self, heading, builder):
        page = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(page)
        outer = QVBoxLayout(page)
        outer.setContentsMargins(12, 18, 18, 14)
        outer.setSpacing(16)
        title = QLabel(heading)
        title.setObjectName("heading")
        outer.addWidget(title)
        builder(outer)
        outer.addStretch()
        self.stack.addWidget(scroll)

    def add_navigation(self, title):
        number = len(self.buttons)
        button = QPushButton(title)
        button.setCheckable(True)
        button.setMinimumHeight(45)
        button.clicked.connect(lambda checked=False, i=number: self.show_page(i))
        self.nav.addWidget(button)
        self.buttons.append(button)

    def show_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.buttons):
            button.setChecked(i == index)

    def persist(self):
        self.circuit.update()
        self.apply_theme()
        if hasattr(self, 'hud'):
            self.sync_hud()

    def cpu_details(self):
        data=self.hud.cpu_gauge.data
        def fmt(value, unit=''):
            return f'{value}{unit}' if value is not None else 'Indisponible'
        lines=[f"Modèle : {data.get('model') or 'Indisponible'}",
               f"Utilisation : {fmt(data.get('usage'), ' %')}",
               f"Fréquence courante : {fmt(data.get('frequency_mhz'), ' MHz')}",
               f"Minimum : {fmt(data.get('min_mhz'), ' MHz')}",
               f"Maximum : {fmt(data.get('max_mhz'), ' MHz')}",
               f"Cœurs physiques : {fmt(data.get('physical'))}",
               f"Threads : {fmt(data.get('logical'))}"]
        for name, readings in data.get('temperatures', {}).items():
            for reading in readings:
                lines.append(f"{name} {reading['label']}: {fmt(reading['c'], ' °C')}")
        QMessageBox.information(self, 'CPU Plugin — Détails', '\\n'.join(lines))

    def sync_hud(self):
        if self.config['plugins'].get('nexus-top-hud', {}).get('enabled', True):
            self.hud.refresh()
            self.hud.show()
        else:
            self.hud.hide()
        cpu=self.config['plugins'].get('cpu-plugin', {})
        self.telemetry.set_interval(cpu.get('refresh_ms', 2000))
        if cpu.get('enabled', True) and self.hud.isVisible():
            self.telemetry.start()
        else:
            self.telemetry.stop()

    def closeEvent(self, event):
        if hasattr(self, 'telemetry'):
            self.telemetry.stop()
        if hasattr(self, 'hud'):
            self.hud.close()
        super().closeEvent(event)

    def general_page(self, lay):
        lay.addWidget(self.label("Comportement du noyau de configuration. Aucun panneau système n'est modifié."))
        for key, title in (("animations", "Animations de l'interface"),
                           ("start_minimized", "Démarrer minimisé (préférence pour le futur lanceur)")):
            control = QCheckBox(title)
            control.setChecked(self.config["general"][key])
            control.toggled.connect(lambda state, k=key: self.set_value("general", k, state))
            lay.addWidget(control)

    def set_value(self, section, key, value):
        self.config[section][key] = value
        self.persist()

    def theme_page(self, lay):
        lay.addWidget(self.label("Couleurs personnalisables et animation des pistes PCB — prévisualisation immédiate."))
        self.color_buttons = {}
        for key, title in (("primary", "Néon principal"),
                           ("secondary", "Néon secondaire"), ("background", "Fond de fenêtre")):
            button = QPushButton()
            self.color_buttons[key] = (button, title)
            button.clicked.connect(lambda checked=False, k=key: self.choose_color(k))
            lay.addWidget(button)
        self.opacity_label = QLabel()
        lay.addWidget(self.opacity_label)
        self.opacity = QSlider(Qt.Horizontal)
        self.opacity.setRange(65, 100)
        self.opacity.setValue(self.config["theme"]["opacity"])
        self.opacity.valueChanged.connect(lambda n: self.set_value("theme", "opacity", n))
        lay.addWidget(self.opacity)
        pcb = QCheckBox("Impulsion lumineuse sur les pistes PCB")
        pcb.setChecked(self.config["theme"]["pcb_effects"])
        pcb.toggled.connect(lambda value: self.set_value("theme", "pcb_effects", value))
        lay.addWidget(pcb)
        reset = QPushButton("↺  Réinitialiser les couleurs")
        reset.clicked.connect(self.reset_colors)
        lay.addWidget(reset)

    def choose_color(self, key):
        initial = QColor(self.config["theme"][key])
        chosen = QColorDialog.getColor(initial, self, "Couleur — " + key)
        if chosen.isValid():
            self.set_value("theme", key, chosen.name().upper())

    def reset_colors(self):
        for key in ("primary", "secondary", "background", "opacity"):
            self.config["theme"][key] = DEFAULT["theme"][key]
        self.opacity.setValue(self.config["theme"]["opacity"])
        self.persist()

    def plugins_page(self, lay):
        lay.addWidget(self.label("Gestionnaire de plugins indépendant. Chaque nouveau manifeste ajoute une rubrique au menu."))
        if not self.plugin_rows:
            lay.addWidget(self.label("Aucun plugin encore installé — prêt pour le premier module."))
        for plugin in self.plugin_rows:
            button = QPushButton(f'{plugin["name"]}  ·  v{plugin["version"]}')
            index = BASE_SECTIONS.__len__() + self.plugin_rows.index(plugin)
            button.clicked.connect(lambda checked=False, i=index: self.show_page(i))
            lay.addWidget(button)

    def plugin_page(self, lay, plugin):
        ident = plugin["id"]
        lay.addWidget(self.label(f'Plugin : {ident}   ·   v{plugin["version"]}'))
        values = self.config["plugins"].setdefault(ident, {})
        for item in plugin["settings"]:
            key = item["key"]
            title = str(item.get("label", key))[:100]
            kind = item["type"]
            if kind == "boolean":
                widget = QCheckBox(title)
                widget.setChecked(bool(values.get(key, item.get("default", False))))
                widget.toggled.connect(lambda v, i=ident, k=key: self.set_plugin(i, k, v))
            elif kind == "integer":
                widget = QSpinBox()
                widget.setRange(max(-100000, int(item.get("min", 0))), min(100000, int(item.get("max", 100))))
                widget.setValue(int(values.get(key, item.get("default", 0))))
                widget.valueChanged.connect(lambda v, i=ident, k=key: self.set_plugin(i, k, v))
                lay.addWidget(self.label(title))
            else:
                widget = QLineEdit(str(values.get(key, item.get("default", ""))))
                widget.setPlaceholderText(title)
                widget.editingFinished.connect(lambda w=widget, i=ident, k=key: self.set_plugin(i, k, w.text()))
                lay.addWidget(self.label(title))
            lay.addWidget(widget)
        if not plugin["settings"]:
            lay.addWidget(self.label("Ce plugin ne propose pas encore de réglages."))

    def set_plugin(self, ident, key, value):
        self.config["plugins"].setdefault(ident, {})[key] = value
        self.persist()

    def updates_page(self, lay):
        lay.addWidget(self.label("Catalogue local du dépôt : Updates/index.json. Sélection manuelle ou dernière version."))
        self.catalog = versions()
        self.version_box = QComboBox()
        if self.catalog:
            for item in self.catalog:
                self.version_box.addItem(item["version"] + "  ·  " + str(item["channel"]))
        else:
            self.version_box.addItem("Aucune version publiée")
        lay.addWidget(self.version_box)
        refresh = QPushButton("↻  Vérifier le catalogue local")
        refresh.clicked.connect(self.refresh_updates)
        lay.addWidget(refresh)
        lay.addWidget(self.label("Version 0.1 : lecture sécurisée du catalogue uniquement. Le téléchargement, la vérification des fichiers et l'installation seront développés séparément ; aucune exécution automatique."))

    def refresh_updates(self):
        self.catalog = versions()
        self.version_box.clear()
        if self.catalog:
            for item in self.catalog:
                self.version_box.addItem(item["version"] + "  ·  " + str(item["channel"]))
        else:
            self.version_box.addItem("Aucune version publiée")

    def about_page(self, lay):
        lay.addWidget(self.label("NOVA NEXUS HD — Cyber-Neon Interactif // THEME 1.0"))
        lay.addWidget(self.label("Noyau de configuration v0.1.0 — PySide6 / Linux Mint XFCE X11"))
        lay.addWidget(self.label("Reconstruction depuis zéro. Les références historiques restent inactives dans Old/."))
        lay.addWidget(self.label("Dépôt : github.com/florian74410/Nova-Nexus-HD---Theme"))

    def apply_theme(self):
        t = self.config["theme"]
        primary, secondary, bg = t["primary"], t["secondary"], t["background"]
        self.circuit.update()
        self.setStyleSheet(f"""
        QWidget {{color:#DCEBFF; font-family:'DejaVu Sans'; font-size:13px;}}
        QFrame#line {{background:{primary};max-height:1px;border:0;}}
        QLabel#brand {{font-size:22px;font-weight:800;color:{primary};letter-spacing:2px;}}
        QLabel#dim {{color:#829BB4;font-size:11px;}}
        QLabel#heading {{color:{primary};font-size:20px;font-weight:700;letter-spacing:1px;}}
        QLabel#description {{color:#B4C7D8;line-height:140%;}}
        QPushButton {{text-align:left; padding:10px 15px; background:#122338;
            border:1px solid #29465F;border-radius:4px;}}
        QPushButton:hover {{border:1px solid {primary};background:#173650;}}
        QPushButton:checked {{color:{primary};border:1px solid {primary};
            border-left:4px solid {secondary};background:#17344B;}}
        QPushButton#close {{font-size:20px;color:{secondary};max-width:40px;text-align:center;}}
        QScrollArea, QScrollArea > QWidget > QWidget {{background:transparent;border:none;}}
        QCheckBox {{spacing:12px;}}
        QSlider::groove:horizontal {{height:5px;background:#28445A;}}
        QSlider::handle:horizontal {{background:{primary};width:15px;margin:-5px 0;}}
        QComboBox, QSpinBox, QLineEdit {{background:#10263A;color:#E4F5FF;
            border:1px solid {primary};padding:8px;}}
        """)
        if hasattr(self, "opacity_label"):
            self.opacity_label.setText("Opacité du fond : " + str(t["opacity"]) + " %")
            for key, (button, title) in self.color_buttons.items():
                button.setText(f"●   {title}  ·  {t[key]}")

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("NOVA NEXUS HD")
    window = Settings()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
