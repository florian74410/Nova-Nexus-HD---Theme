# Old — archives techniques v1.1

Source: https://github.com/florian74410/Health-and-Perfs---Navigation-Controler-Bar/tree/release/nova-nexus-hd-v1.1.0
Commit source initial: `7d1aada088a4f7fd7319ca110e8ce68c3f476a5a`

Ces fichiers sont des **références historiques non actives**, et non des composants prêts à intégrer à la nouvelle application. Ne jamais importer directement ce dossier dans le runtime ou lancer ses scripts d'installation.

## Sélection

- Visuels et identité: `Assets/` + `src/healthbar/assets/` (PCB, fond bleu, logo et références de licences).
- Thèmes / fenêtres: `src/nova_nexus/theme_*.py`, `desktop_theme.py`, `window_controls.py`, `cockpit_style.py`.
- Plugins: `plugins.py`, `plugin_manager.py`, `plugin_sources.py`, `bundled_plugins.py`, documentation.
- Mises à jour: `updates.py`, `update_recovery.py` (modèles de récupération uniquement; réécrire le protocole de publication).
- UI: `dialogs.py`, `terminal_manager.py`, `config.py` à extraire sélectivement.

## Règles pour la reconstruction

1. Nouveau projet, nouveau runtime et nouveaux tests, sans héritage implicite.
2. Jamais de désactivation/masquage de panneaux XFCE par défaut; retour au natif systématique en cas de désactivation.
3. `Update/` du nouveau dépôt: index versionné + manifestes signés ou SHA-256 vérifiés, choix de version, confirmation et rollback.
4. Plugins développés un par un avec API versionnée, isolation, permissions et paramètres propres sous Paramètres > Plugins.
5. Revoir les licences pour les icônes tierces et les dépendances avant diffusion.

## Inventaire archivé

- `Old/Assets/Overlays/nova_pcb_overlay.svg`
- `Old/Assets/Wallpapers/nova-electric-blue-pcb.svg`
- `Old/src/healthbar/assets/novabar-icon.svg`
- `Old/src/nova_nexus/assets/nova-close.svg`
- `Old/src/nova_nexus/theme_engine.py`
- `Old/src/nova_nexus/theme_pack.py`
- `Old/src/nova_nexus/theme_settings.py`
- `Old/src/nova_nexus/window_controls.py`
- `Old/src/healthbar/cockpit_style.py`
- `Old/src/healthbar/plugin_manager.py`
- `Old/src/healthbar/plugin_sources.py`
- `Old/src/healthbar/plugins.py`
- `Old/src/healthbar/updates.py`
- `Old/src/healthbar/update_recovery.py`
- `Old/src/healthbar/bundled_plugins.py`
- `Old/docs/PLUGINS.md`
- `Old/docs/NOVA_THEME_PACK_INTEGRATION.md`
- `Old/src/nova_nexus/desktop_theme.py`
- `Old/src/nova_nexus/wallpapers.py`
- `Old/src/healthbar/assets/icons/README.md`
- `Old/src/healthbar/assets/icons/SOURCES.json`
- `Old/src/nova_nexus/terminal_manager.py`
- `Old/src/healthbar/dialogs.py`
- `Old/src/healthbar/config.py`
