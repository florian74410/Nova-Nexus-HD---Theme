"""Persistent NOVA theme editor; desktop export remains a separate explicit action."""
from PySide6 import QtWidgets as W
from .theme_engine import PALETTES, preset, get_active_theme, set_active_theme, qt_stylesheet


class ThemeSettings(W.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('NOVA NEXUS HD · Thème')
        self.theme = get_active_theme()
        self.setStyleSheet(qt_stylesheet(self.theme))
        root = W.QVBoxLayout(self)
        form = W.QFormLayout()
        root.addLayout(form)
        self.palette = W.QComboBox()
        self.palette.addItems(PALETTES)
        self.palette.setCurrentText(self.theme['name'])
        self.mode = W.QComboBox()
        self.mode.addItems(['Off', 'Eco', 'Standard', 'Ultra'])
        self.mode.setCurrentText('Standard')
        form.addRow('Palette', self.palette)
        form.addRow('Effets prédéfinis', self.mode)
        apply_preset = W.QPushButton('Charger cette palette et ces effets')
        apply_preset.clicked.connect(self.load_preset)
        form.addRow(apply_preset)
        self.colors={}
        for key,label in (('primary','Couleur principale'),('secondary','Couleur secondaire'),('danger','Symboles de fenêtre'),('background','Fond')):
            control=W.QLineEdit(self.theme['colors'][key]);self.colors[key]=control
            form.addRow(label,control)
        self.controls = {}
        for key, label, lo, hi, step in (
            ('opacity', 'Opacité du fond', .4, 1, .05),
            ('glass_opacity','Opacité du verre',.4,1,.05),
            ('reflection_intensity','Reflets',0,1,.05),
            ('font_scale','Échelle du texte',.75,2,.05),
            ('animation_speed','Vitesse des animations',.25,3,.25),
            ('glow', 'Halo', 0, 1, .05), ('shadow', 'Ombre', 0, 1, .05),
            ('pcb_visibility', 'Visibilité PCB', 0, 1, .05),
            ('border_width', 'Épaisseur du contour', .5, 5, .5),
            ('bevel_size', 'Biseau', 0, 30, 1)):
            control = W.QDoubleSpinBox()
            control.setRange(lo, hi); control.setSingleStep(step)
            self.controls[key] = control
            form.addRow(label, control)
        self.motion = W.QCheckBox('Animations activées')
        form.addRow(self.motion)
        self.duration = W.QSpinBox(); self.duration.setRange(0, 1200)
        form.addRow('Durée des transitions (ms)', self.duration)
        self.populate()
        buttons = W.QDialogButtonBox(W.QDialogButtonBox.Save | W.QDialogButtonBox.Cancel | W.QDialogButtonBox.RestoreDefaults)
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        buttons.button(W.QDialogButtonBox.RestoreDefaults).clicked.connect(self.reset)
        root.addWidget(W.QLabel('Les nouvelles fenêtres utilisent ces réglages.\nRéappliquer le bureau NOVA pour exporter les décorations GTK/XFWM.'))
        root.addWidget(buttons)

    def populate(self):
        for key,control in self.colors.items():control.setText(self.theme['colors'][key])
        for key, control in self.controls.items(): control.setValue(self.theme['effects'][key])
        self.motion.setChecked(self.theme['motion']['enabled'])
        self.duration.setValue(self.theme['motion']['duration_ms'])

    def load_preset(self):
        self.theme = preset(self.palette.currentText(), self.mode.currentText())
        self.populate()

    def reset(self):
        self.theme = preset(); self.palette.setCurrentText('Electric Blue'); self.populate()

    def save(self):
        for key,control in self.colors.items():self.theme["colors"][key]=control.text()
        for key, control in self.controls.items(): self.theme['effects'][key] = control.value()
        self.theme['motion']['enabled'] = self.motion.isChecked()
        self.theme['motion']['duration_ms'] = self.duration.value()
        try: set_active_theme(self.theme)
        except (OSError, ValueError) as error:
            W.QMessageBox.warning(self, 'NOVA', str(error)); return
        self.accept()
