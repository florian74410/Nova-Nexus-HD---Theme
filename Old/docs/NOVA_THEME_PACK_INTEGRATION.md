> Mise à jour 0.7.0 : les composants sont maintenant intégrés au runtime et au pack natif. Voir [le guide actuel](UPDATE_V070.md). Les limitations de notification et de compatibilité indiquées dans ce document restent à vérifier par composant.

# NOVA NEXUS HD — Theme Pack integration (preview)

The complete **visual concept** consists of existing NovaBar v0.6.11:
top monitoring bar, bottom cockpit bar, and two side docks,
plus NOVA Explorer, NOVA Glass dialogs and notification-style previews,
GTK/XFWM4 theme and wallpaper assets in this development branch.

## What is wired today

- NovaBar 0.6.11 runs the four existing desktop bars/docks; this feature branch
  does **not** replace or reconfigure them.
- The Python module `nova_nexus.theme_pack` installs an optional desktop launcher
  for NOVA Explorer. Explorer uses the NOVA Glass dialog component.
- NOVA Glass notification preview uses the same style and shared theme tokens.
- GTK/XFWM4 assets and wallpaper are copied/exported to user-owned paths.
  No theme is activated automatically.
- The existing NovaBar Upgrade channel is **unchanged**. This is a preview pack,
  not yet a complete signed and verified auto-updatable installer.

## Test on Macro

From your clean clone and active virtual environment:

```bash
git pull --ff-only origin feature/nova-nexus-hd-foundation
python3 -m unittest discover -s tests -p 'test_nova_*.py' -v
python3 -m nova_nexus.theme_pack --install
python3 -m nova_nexus.explorer
python3 -m nova_nexus.theme_pack --preview-notification
```

Remove only the NOVA Explorer launcher:

```bash
python3 -m nova_nexus.theme_pack --remove-launcher
```

The `--install` preview does not switch GTK/XFWM4 appearance,
default file manager, notification daemon, login/lock screen or panel ownership.
NovaBar 0.6.11 continues displaying its two bars and side docks, independently.

## Production release blockers

- Combine sources into the actual NovaBar native package and install user-space
  Python dependencies without relying on an ad-hoc venv path.
- Validate release packaging, updater manifest, dependencies, and rollback.
- Complete notifications D-Bus integration with XFCE fallback and only one owner.
- Validate LightDM / session locker separately before enabling cosmetic changes.
- Perform usability, multi-workspace and graphical tests on Macro before merging.
