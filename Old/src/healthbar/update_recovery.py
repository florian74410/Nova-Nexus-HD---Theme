"""Backup user data before switching versions and restore a tested prior runtime."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
from .config import data_dir, Settings
from .profiles import workspace_dir, write_json
from .install_engine import install_root, read_installed_state, payload_executable, self_test


def backup_user_data(root=None):
    root = Path(root) if root else install_root()
    destination = root / 'update-backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination.mkdir(parents=True)
    sources = {'config': data_dir(), 'workspace': workspace_dir()}
    for name, source in sources.items():
        target = destination / name
        target.mkdir()
        if source.is_dir():
            for item in source.iterdir():
                # Runtime and backup folders are outside the user configuration set.
                if item.name in ('runtime', 'Documents', 'update-backups') or item.resolve() == root.resolve():
                    continue
                if item.is_symlink():
                    continue
                if item.is_dir(): shutil.copytree(item, target/item.name, symlinks=True)
                elif item.is_file(): shutil.copy2(item, target/item.name)
    state = read_installed_state(root)
    write_json(destination / 'installation.json', state)
    return destination


def rollback(root=None):
    root = Path(root) if root else install_root()
    current = read_installed_state(root)
    previous = (current or {}).get('previous')
    backup = Path((current or {}).get('recovery_backup', ''))
    if not previous or not previous.get('executable'):
        raise ValueError('Aucun runtime précédent restaurable')
    executable = payload_executable(root/'versions'/previous['version'])
    if executable is None or executable.resolve() != Path(previous['executable']).resolve():
        raise ValueError('Le runtime précédent est absent ou extérieur aux versions gérées')
    if not backup.is_dir() or not backup.resolve().is_relative_to((root/'update-backups').resolve()):
        raise ValueError('Sauvegarde de restauration indisponible')
    self_test(executable, backup/'rollback.log', expected_version=previous['version'])
    # Activation is transactional. Keep the current runtime and a fresh backup too.
    fresh = backup_user_data(root)
    from .install_engine import activate
    state = activate(executable, Settings.load(), {}, previous.get('desktop_shortcut', False),
                     root, release_version=previous['version'])
    try:
        for name, target in (('config', data_dir()), ('workspace', workspace_dir())):
            saved = backup/name
            for item in saved.iterdir():
                if item.is_dir(): shutil.copytree(item, target/item.name, dirs_exist_ok=True, symlinks=True)
                elif item.is_file():
                    target.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, target/item.name)
        from .autostart import set_enabled
        set_enabled(Settings.load().autostart, command=[str(executable)])
        state.update(recovery_backup=str(fresh), rollback_requested=True)
        write_json(root/'installation.json', state)
    except Exception:
        # Restore activation so a failed data restore cannot leave stale metadata.
        write_json(root/'installation.json', current)
        from .install_engine import write_shortcuts
        write_shortcuts(Path(current['executable']), current.get('desktop_shortcut',False), root)
        raise
    return state
