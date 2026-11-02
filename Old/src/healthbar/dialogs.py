from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QFormLayout, QComboBox,
    QSpinBox, QSlider, QCheckBox, QDialogButtonBox, QPushButton, QFileDialog,
    QMessageBox, QListWidget, QHBoxLayout, QTabWidget, QWidget, QLineEdit)
from . import __version__
from .autostart import set_enabled
from .plugins import PluginRegistry

STYLE = """
QDialog { background: #061224; color: #dfedff; }
QTabWidget::pane { border: 1px solid #17639b; border-radius: 8px; padding: 15px; }
QTabBar::tab { color: #c6eaff; padding: 10px 13px; background: #091b32; border: 1px solid #17639b; }
QTabBar::tab:selected { background: #104377; color: #31dcff; border-bottom: 2px solid #21ceff; }
QLineEdit { color: #e4f2ff; background: #0b2440; border: 1px solid #17639b; padding: 8px; }
QLabel, QCheckBox { color: #c4d9f7; font-size: 13px; }
QLabel#title { color: #31dcff; font-size: 25px; font-weight: 700; }
QPushButton, QComboBox, QSpinBox { color: #dcecff; background: #0b2440;
 border: 1px solid #17639b; border-radius: 6px; padding: 9px; }
QPushButton:hover { border-color: #00ddff; background: #123960; }
QPushButton:disabled { color: #65798c; border-color: #19314a; }
QListWidget { background: #040d1b; color: #dcecff; border: 1px solid #17639b; padding: 8px; }
QSlider::groove:horizontal { height: 4px; background: #17476c; }
QSlider::handle:horizontal { width: 16px; margin: -6px 0; background: #14d8ff; border-radius: 8px; }
QCheckBox { spacing: 12px; }
"""


class SettingsDialog(QDialog):
    def customize_nova(self):
        from nova_nexus.theme_settings import ThemeSettings
        ThemeSettings(self).exec()

    def configure_nova(self, action):
        from .nova_components import configure_theme
        try:
            configure_theme(action)
            from .config import Settings
            self.settings.__dict__.update(Settings.load().__dict__)
            self.accept()
        except Exception as error:
            QMessageBox.warning(self,"Bureau NOVA",str(error))

    def __init__(self, settings, screens, first_run=False, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Installation • Health & Perfs" if first_run else "Préférences • Health & Perfs")
        from .ui_kit import stylesheet
        self.setStyleSheet(stylesheet(STYLE))
        self.setMinimumWidth(630)
        self.resize(710, 630)
        box = QVBoxLayout(self)
        box.setContentsMargins(30, 26, 30, 26)
        box.setSpacing(20)
        title = QLabel("BIENVENUE À BORD" if first_run else "VOTRE BARRE. VOS RÈGLES.")
        title.setObjectName("title")
        box.addWidget(title)
        intro = QLabel("Health & Perfs  /  Navigation Controller Bar  /  v"+__version__
            + "\nInstallation pour votre session utilisateur. Les autres comptes\nconservent leurs propres préférences et extensions.")
        intro.setWordWrap(True)
        box.addWidget(intro)
        form = QFormLayout()
        form.setVerticalSpacing(16)
        self.position = QComboBox()
        self.position.addItems(["Haut", "Bas", "Droite • verticale", "Gauche • verticale"])
        self.position.setCurrentIndex(("top", "bottom", "right", "left").index(settings.position))
        form.addRow("Placement", self.position)
        self.screen = QComboBox()
        self.screen.addItems([f"Écran {i+1} • {s.name()}" for i, s in enumerate(screens)])
        self.screen.setCurrentIndex(min(settings.screen, len(screens)-1))
        form.addRow("Écran", self.screen)
        self.thickness = QSpinBox()
        self.thickness.setRange(50, 150)
        self.thickness.setValue(settings.thickness)
        self.thickness.setSuffix(" px")
        form.addRow("Épaisseur", self.thickness)
        self.opacity = QSlider(Qt.Orientation.Horizontal)
        self.opacity.setRange(0, 100)
        self.opacity.setValue(settings.opacity)
        self.opacity_label = QLabel(f"{settings.opacity} %")
        self.opacity.valueChanged.connect(lambda v: self.opacity_label.setText(f"{v} %"))
        row = QHBoxLayout()
        row.addWidget(self.opacity)
        row.addWidget(self.opacity_label)
        form.addRow("Opacité des modules", row)
        self.auto_hide = QCheckBox("Rétracter après 15 s sans survol")
        self.auto_hide.setChecked(settings.auto_hide)
        self.retract_mode = QComboBox()
        for label, key in (("Always visible", "always"), ("Auto retract", "auto"), ("Manual retract only", "manual")):
            self.retract_mode.addItem(label, key)
        self.retract_mode.setCurrentIndex(max(0, self.retract_mode.findData(settings.retract_mode or ("auto" if settings.auto_hide else "manual"))))
        form.addRow("Rétractation", self.retract_mode)
        self.always_on_top = QCheckBox("Always-on-top (selon le compositeur)")
        self.always_on_top.setChecked(settings.always_on_top)
        form.addRow("Priorité", self.always_on_top)
        self.autostart = QCheckBox("Lancer à l’ouverture de ma session")
        self.autostart.setChecked(settings.autostart)
        if __import__("os").environ.get("NOVABAR_PACKAGED") == "flatpak":
            self.autostart.setEnabled(False)
            self.autostart.setToolTip("Démarrage automatique non géré dans cette édition Flatpak.")
        
        self.hide_seconds = QSpinBox()
        self.hide_seconds.setRange(3, 120)
        self.hide_seconds.setValue(settings.hide_seconds)
        self.hide_seconds.setSuffix(" secondes")
        form.addRow("Délai avant veille", self.hide_seconds)
        self.retracted_hud_height = QSpinBox()
        self.retracted_hud_height.setRange(20, 50)
        self.retracted_hud_height.setValue(settings.retracted_hud_height)
        self.retracted_hud_height.setSuffix(" px")
        form.addRow("Hauteur HUD rétracté", self.retracted_hud_height)
        self.length_percent = QSpinBox()
        self.length_percent.setRange(25, 100)
        self.length_percent.setValue(settings.length_percent)
        self.length_percent.setSuffix(" % écran")
        form.addRow("Longueur", self.length_percent)
        self.alignment = QComboBox()
        self.alignment.addItems(["Left", "Middle", "Right"])
        self.alignment.setCurrentIndex(("left", "center", "right").index(settings.alignment))
        form.addRow("Alignement", self.alignment)
        tabs = QTabWidget()
        general = QWidget()
        general_form = QFormLayout(general)
        general_form.addRow("Démarrage", self.autostart)
        self.refresh_seconds = QSpinBox()
        self.refresh_seconds.setRange(1, 30)
        self.refresh_seconds.setSuffix(" s")
        self.refresh_seconds.setValue(settings.refresh_seconds)
        general_form.addRow("Actualisation", self.refresh_seconds)
        self.shell_dir = QLineEdit(settings.shell_dir)
        self.shell_dir.setPlaceholderText("~/Scripts/HardwareHealth")
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.shell_dir)
        browse = QPushButton("Parcourir")
        browse.clicked.connect(self.choose_script_folder)
        folder_row.addWidget(browse)
        general_form.addRow("Dossier Shell", folder_row)
        from .ui_kit import THEMES
        self.theme = QComboBox()
        for key, label in THEMES.items(): self.theme.addItem(label, key)
        self.theme.setCurrentIndex(max(0, self.theme.findData(settings.theme)))
        general_form.addRow("Thème actif", self.theme)
        self.holo_enabled=QCheckBox("Ouvrir les panneaux par clic sur le logo du plugin")
        self.holo_enabled.setChecked(settings.holo_enabled)
        general_form.addRow("Holo",self.holo_enabled)
        update_button = QPushButton("Upgrade • mise à jour automatique")
        update_button.clicked.connect(self.open_updates)
        general_form.addRow("NOVA NEXUS HD", update_button)
        from .help_links import WIKI_URL
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        wiki_button = QPushButton("📖 Ouvrir le Wiki NovaBar")
        wiki_button.setToolTip("Guide : installation, interface, capteurs, plugins, dépannage")
        wiki_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(WIKI_URL)))
        general_form.addRow("Documentation", wiki_button)
        installer_button = QPushButton("Profil, confidentialité et raccourcis…")
        installer_button.clicked.connect(self.open_installer)
        if __import__("os").environ.get("NOVABAR_PACKAGED") in ("deb", "flatpak"):
            installer_button.setEnabled(False)
            installer_button.setToolTip("Le paquet Linux gère les fichiers du programme ; utiliser les préférences et le gestionnaire de plugins.")
        general_form.addRow("NovaBar", installer_button)
        # All three independent panels live in the same NovaBar executable.
        docks = QWidget()
        docks_layout = QVBoxLayout(docks)
        docks_layout.addWidget(QLabel("NOVABAR • QUATRE PANNEAUX INDÉPENDANTS"))
        docks_layout.addWidget(QLabel("Chaque panneau peut être activé séparément. Les colonnes se cachent après 3 secondes. Elles s’ouvrent dans les 10 px du bord, sans trait visible."))
        self.hud_enabled = QCheckBox("Barre principale • télémétrie CPU/GPU/RAM/SSD")
        self.hud_enabled.setChecked(settings.hud_enabled)
        docks_layout.addWidget(self.hud_enabled)
        self.dock_left_enabled = QCheckBox("Dock gauche actif")
        self.dock_left_enabled.setChecked(settings.dock_left_enabled)
        docks_layout.addWidget(self.dock_left_enabled)
        self.dock_right_enabled = QCheckBox("Dock droit actif")
        self.dock_right_enabled.setChecked(settings.dock_right_enabled)
        docks_layout.addWidget(self.dock_right_enabled)
        self.bottom_dock_enabled = QCheckBox("Barre inférieure CYBER NEXUS • applications, fenêtres et système")
        self.bottom_dock_enabled.setChecked(settings.bottom_dock_enabled)
        self.bottom_dock_enabled.setEnabled(__import__("sys").platform.startswith("linux"))
        docks_layout.addWidget(self.bottom_dock_enabled)
        self.bottom_dock_height = QSpinBox()
        self.bottom_dock_height.setRange(60, 112)
        self.bottom_dock_height.setSuffix(" px")
        self.bottom_dock_height.setValue(settings.bottom_dock_height)
        docks_layout.addWidget(QLabel("Hauteur du cockpit inférieur"))
        docks_layout.addWidget(self.bottom_dock_height)
        self.dock_left_kind = QComboBox()
        self.dock_left_kind.addItem("Dossiers personnels", "folders")
        self.dock_left_kind.addItem("Applications du Bureau", "apps")
        self.dock_left_kind.setCurrentIndex(max(0, self.dock_left_kind.findData(settings.dock_left_kind)))
        docks_layout.addWidget(QLabel("Contenu du dock gauche (l'autre dock reçoit automatiquement l'autre contenu) :"))
        docks_layout.addWidget(self.dock_left_kind)
        docks_layout.addWidget(QLabel("⠿ Glissez la poignée d'un dock vers le bord opposé ou cliquez ↔ pour échanger les deux."))
        docks_layout.addWidget(QLabel("Glissez des dossiers depuis Thunar ou des lanceurs .desktop du Bureau pour les ajouter ou les réorganiser."))
        docks_layout.addWidget(QLabel("Les raccourcis sont conservés dans votre profil NovaBar ; aucun fichier n'est déplacé ou effacé."))
        docks_layout.addStretch()
        display = QWidget()
        display.setLayout(form)
        edit = QWidget()
        editor = QVBoxLayout(edit)
        editor.addWidget(QLabel("ÉDITION DU HUD • réglages rapides"))
        tip = QLabel("La présentation se compacte automatiquement lorsque la longueur diminue.")
        tip.setWordWrap(True)
        editor.addWidget(tip)
        reset = QPushButton("Rétablir l'affichage d'origine")
        reset.clicked.connect(self.reset_display)
        editor.addWidget(reset)
        editor.addStretch()
        extensions = QWidget()
        ext_layout = QVBoxLayout(extensions)
        ext_layout.addWidget(QLabel("Importer des ZIP v2, activer les plugins et restaurer une version."))
        open_ext = QPushButton("OUVRIR LE PLUGIN MANAGER")
        open_ext.clicked.connect(lambda: PluginsDialog(PluginRegistry(), self).exec())
        ext_layout.addWidget(open_ext)
        ext_layout.addStretch()
        help_tab = QWidget()
        help_layout = QVBoxLayout(help_tab)
        howto = QLabel("Bord de l'écran : révéler la barre\nFlèche haute : minimiser\nLogo en haut à droite : ouvrir/fermer le Holo\nCPU Mode : selon noyau et permissions\nZIP : code jamais exécuté automatiquement")
        howto.setWordWrap(True)
        help_layout.addWidget(howto)
        help_layout.addStretch()
        wiki = QWidget()
        wiki_layout = QVBoxLayout(wiki)
        description = QLabel("Documentation NovaBar : installation, configuration, capteurs et extensions. Ces liens s’ouvrent dans le navigateur ; cette base accueillera un viewer intégré.")
        description.setWordWrap(True); wiki_layout.addWidget(description)
        from .help_links import DOC_LINKS
        for label, url in DOC_LINKS.items():
            button = QPushButton(label)
            button.clicked.connect(lambda checked=False, url=url: QDesktopServices.openUrl(QUrl(url)))
            wiki_layout.addWidget(button)
        wiki_layout.addStretch()
        tabs.addTab(wiki, "Wiki")
        tabs.addTab(docks, "Docks")
        modules_tab = QWidget()
        modules_layout = QVBoxLayout(modules_tab)
        title_modules = QLabel("MODULES DE LA BARRE PRINCIPALE")
        modules_layout.addWidget(title_modules)
        modules_description = QLabel(
            "Décochez les plugins à masquer sur cette machine. "
            "Les modules restent installés, leurs mesures ne sont pas supprimées. "
            "Le module Power affiche uniquement les données réellement disponibles.")
        modules_description.setWordWrap(True)
        modules_layout.addWidget(modules_description)
        from .hud import HudCanvas
        labels = {
            "cpu": "CPU — Fréquence et température",
            "gpu": "GPU — Fréquence et utilisation",
            "ram": "RAM — Utilisation et capacité",
            "storage": "Stockage — SSD / HDD",
            "fans": "Ventilateurs — RPM",
            "network": "Réseau — Débits et ping",
            "power": "Power ⚡ — Consommation et tensions",
        }
        self.module_checks = {}
        for slot, name in labels.items():
            control = QCheckBox(name)
            control.setChecked(slot not in settings.hidden_modules)
            self.module_checks[slot] = control
            modules_layout.addWidget(control)
        modules_layout.addStretch()
        tabs.addTab(modules_tab, "Modules")
        nova_tab=QWidget();nova_layout=QVBoxLayout(nova_tab)
        nova_info=QLabel("NOVA NEXUS HD\nActive le HUD, les deux panneaux latéraux et le cockpit inférieur.\nNOVA Explorer reste accessible sans remplacer le gestionnaire de dossiers choisi.\nLes applications GTK3 compatibles reçoivent le thème NOVA.\nLes notifications XFCE restent actives ; le style NOVA est disponible en aperçu.")
        nova_info.setWordWrap(True);nova_layout.addWidget(nova_info)
        for label,action in (("Activer le bureau NOVA NEXUS HD","apply"),("Restaurer les préférences précédentes","restore")):
            control=QPushButton(label);control.setEnabled(__import__("sys").platform.startswith("linux"))
            control.clicked.connect(lambda checked=False,a=action:self.configure_nova(a));nova_layout.addWidget(control)
        customize=QPushButton("Personnaliser le thème NOVA")
        customize.clicked.connect(self.customize_nova)
        nova_layout.addWidget(customize)
        notifications=QPushButton("Centre de notifications NOVA")
        notifications.clicked.connect(lambda:__import__('nova_nexus.notification_center',fromlist=['center']).center().show_history())
        nova_layout.addWidget(notifications)
        explorer=QPushButton("Ouvrir NOVA Explorer")
        explorer.clicked.connect(lambda:__import__("healthbar.nova_components",fromlist=["open_explorer"]).open_explorer(__import__("pathlib").Path.home()))
        nova_layout.addWidget(explorer);nova_layout.addStretch();tabs.addTab(nova_tab,"Bureau NOVA")
        xfce_tab = QWidget()
        xfce_layout = QVBoxLayout(xfce_tab)
        info = QLabel("XFCE CYBER SKIN • Habillage du panneau natif")
        xfce_layout.addWidget(info)
        explanation = QLabel("Conserve les icônes et les fenêtres du panneau XFCE original. "
                             "Ajoute un habillage PCB avec impulsions animées, modifie au choix son épaisseur "
                             "(sans jamais dépasser 2 fois l'originale) et le masque automatiquement "
                             "après le délai choisi. Le bord natif de 1 px assure le rappel au survol.")
        explanation.setWordWrap(True)
        xfce_layout.addWidget(explanation)
        self.xfce_skin_enabled = QCheckBox("Activer l'habillage CYBER NEXUS du panneau XFCE inférieur")
        self.xfce_skin_enabled.setChecked(settings.xfce_skin_enabled)
        xfce_layout.addWidget(self.xfce_skin_enabled)
        delay_info = QLabel("La temporisation commence après avoir quitté le panneau. "
                            "Les paramètres de rétraction et d'épaisseur d'origine sont sauvegardés.")
        delay_info.setWordWrap(True)
        xfce_layout.addWidget(delay_info)
        self.xfce_skin_delay_seconds = QSpinBox()
        self.xfce_skin_delay_seconds.setRange(1, 120)
        self.xfce_skin_delay_seconds.setSuffix(" secondes")
        self.xfce_skin_delay_seconds.setValue(settings.xfce_skin_delay_seconds)
        xfce_layout.addWidget(QLabel("Délai avant rétractation complète"))
        xfce_layout.addWidget(self.xfce_skin_delay_seconds)
        self.xfce_skin_scale_percent = QSlider(Qt.Orientation.Horizontal)
        self.xfce_skin_scale_percent.setRange(100, 200)
        self.xfce_skin_scale_percent.setValue(settings.xfce_skin_scale_percent)
        self.xfce_skin_scale_label = QLabel(
            f"Épaisseur : {settings.xfce_skin_scale_percent} % de l'originale (max. 200 %)")
        self.xfce_skin_scale_percent.valueChanged.connect(
            lambda number: self.xfce_skin_scale_label.setText(
                f"Épaisseur : {number} % de l'originale (max. 200 %)"))
        xfce_layout.addWidget(self.xfce_skin_scale_label)
        xfce_layout.addWidget(self.xfce_skin_scale_percent)
        self.xfce_skin_fx_intensity = QSlider(Qt.Orientation.Horizontal)
        self.xfce_skin_fx_intensity.setRange(0, 100)
        self.xfce_skin_fx_intensity.setValue(settings.xfce_skin_fx_intensity)
        self.xfce_skin_fx_label = QLabel(f"Effets lumineux : {settings.xfce_skin_fx_intensity} %")
        self.xfce_skin_fx_intensity.valueChanged.connect(
            lambda amount: self.xfce_skin_fx_label.setText(f"Effets lumineux : {amount} %"))
        xfce_layout.addWidget(self.xfce_skin_fx_label)
        xfce_layout.addWidget(self.xfce_skin_fx_intensity)
        xfce_note = QLabel("L'ajout d'icônes reste géré par le panneau XFCE : clic droit sur le panneau "
                           "→ Panneau → Ajouter de nouveaux éléments. Désactiver l'habillage restaure "
                           "l'apparence et le comportement de repli précédents.")
        xfce_note.setWordWrap(True)
        xfce_layout.addWidget(xfce_note)
        xfce_layout.addStretch()
        tabs.addTab(xfce_tab, "XFCE Cyber")
        for name, widget in (("Générale", general), ("Affichage", display),
                              ("Édition", edit), ("Extensions", extensions), ("Aide", help_tab)):
            tabs.addTab(widget, name)
        box.addWidget(tabs, 1)
        note = QLabel("Mesures locales : — indique un capteur indisponible.\nPriorité d’affichage limitée par le système et son compositeur.")
        note.setWordWrap(True)
        box.addWidget(note)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Save).setText("Installer et ouvrir" if first_run else "Enregistrer")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)
        box.addWidget(buttons)

    def open_updates(self):
        from .updates import UpdateDialog
        UpdateDialog(self, auto_upgrade=True).exec()

    def open_installer(self):
        from .installer import InstallerWizard
        from .profiles import workspace_dir, current_profile
        import json
        wizard = InstallerWizard(self.settings, parent=self)
        path = workspace_dir() / "App/Profiles" / (current_profile() + ".json")
        if path.is_file():
            record = json.loads(path.read_text(encoding="utf-8"))
            identity = record.get("identity", {})
            wizard.email.setText(identity.get("email", ""))
            wizard.username.setText(identity.get("username", ""))
            wizard.share.setChecked(identity.get("share_experience", False))
        # Editing the profile uses the first page and preserves installed runtime files.
        def save_profile_settings():
            from .profiles import save_profile
            from dataclasses import asdict, replace
            if wizard.stack.currentIndex() == 0:
                wizard.advance()
                if wizard.stack.currentIndex() == 1:
                    wizard.next.setText("ENREGISTRER")
            elif wizard.stack.currentIndex() == 1:
                try:
                    changed = replace(self.settings, position=wizard.position.currentData(),
                        thickness=wizard.thickness.value(), length_percent=wizard.length.value(),
                        opacity=wizard.opacity.value(), auto_hide=wizard.retract_mode.currentData()=="auto", retract_mode=wizard.retract_mode.currentData(),
                        theme=wizard.theme.currentData(),always_on_top=wizard.always_on_top.isChecked(),holo_enabled=wizard.holo_enabled.isChecked(),
                        autostart=wizard.autostart.isChecked(), shortcuts=wizard.bindings()).validate()
                    set_enabled(changed.autostart)
                    changed.save()
                    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
                    save_profile(wizard.identity, asdict(changed), previous.get("installation"))
                    self.settings.__dict__.update(changed.__dict__)
                    wizard.accept()
                except (ValueError, OSError) as error:
                    QMessageBox.warning(wizard, "Profil", str(error))
        wizard.next.clicked.disconnect()
        wizard.next.clicked.connect(save_profile_settings)
        wizard.autostart.setChecked(self.settings.autostart)
        wizard.next.setText("VALIDER")
        if wizard.exec() == QDialog.DialogCode.Accepted:
            self.accept()

    def choose_script_folder(self):
        chosen = QFileDialog.getExistingDirectory(self, "Dossier de scripts Shell", self.shell_dir.text())
        if chosen:
            self.shell_dir.setText(chosen)

    def reset_display(self):
        self.length_percent.setValue(100)
        self.thickness.setValue(72)
        self.opacity.setValue(88)
        self.hide_seconds.setValue(15)
        self.retracted_hud_height.setValue(30)

    def save(self):
        from dataclasses import replace
        updated = replace(self.settings, position=("top", "bottom", "right", "left")[self.position.currentIndex()],
            screen=self.screen.currentIndex(), thickness=self.thickness.value(), opacity=self.opacity.value(),
            auto_hide=self.retract_mode.currentData() == "auto", retract_mode=self.retract_mode.currentData(),
            always_on_top=self.always_on_top.isChecked(), theme=self.theme.currentData(), holo_enabled=self.holo_enabled.isChecked(), hide_seconds=self.hide_seconds.value(), retracted_hud_height=self.retracted_hud_height.value(),
            autostart=self.autostart.isChecked(), configured=True,
            length_percent=self.length_percent.value(),
            alignment=("left", "center", "right")[self.alignment.currentIndex()],
            refresh_seconds=self.refresh_seconds.value(), shell_dir=self.shell_dir.text().strip(),
            hud_enabled=self.hud_enabled.isChecked(),
            dock_left_enabled=self.dock_left_enabled.isChecked(),
            dock_right_enabled=self.dock_right_enabled.isChecked(),
            bottom_dock_enabled=self.bottom_dock_enabled.isChecked(),
            bottom_dock_height=self.bottom_dock_height.value(),
            dock_left_kind=self.dock_left_kind.currentData(),
            dock_right_kind="apps" if self.dock_left_kind.currentData() == "folders" else "folders",
            hidden_modules=[slot for slot, checkbox in self.module_checks.items()
                            if not checkbox.isChecked()],
            xfce_skin_enabled=self.xfce_skin_enabled.isChecked(),
            xfce_skin_delay_seconds=self.xfce_skin_delay_seconds.value(),
            xfce_skin_scale_percent=self.xfce_skin_scale_percent.value(),
            xfce_skin_fx_intensity=self.xfce_skin_fx_intensity.value())
        try:
            set_enabled(updated.autostart)
            updated.save()
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Enregistrement impossible", str(error))
            return
        self.settings.__dict__.update(updated.__dict__)
        self.accept()


# Plugin Manager v0.3.3 uses one compact two-tab dialog, independent of the installer.
# Import here keeps the existing app/settings interface stable.
from .plugin_manager import PluginsDialog
