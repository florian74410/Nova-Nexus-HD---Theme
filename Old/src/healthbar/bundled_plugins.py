"""Synchronize bundled data-only sensors without changing activation choices."""
from pathlib import Path
from .plugins import PluginRegistry, version_tuple


def bundled_archives():
    return sorted((Path(__file__).parent/'assets/plugins').glob('*.zip'))


def seed_bundled_plugins(settings):
    registry = PluginRegistry()
    installed = {item['id']: item for item in registry.installed()}
    for archive in bundled_archives():
        manifest, digest = registry.inspect(archive)
        current = installed.get(manifest['id'])
        if current:
            # Only an identical first-party declaration may be upgraded automatically.
            # A custom plugin with the same ID and newer versions remain authoritative.
            before = {k: v for k, v in current.items() if k not in ('version', 'enabled')}
            after = {k: v for k, v in manifest.items() if k != 'version'}
            if before != after or version_tuple(current['version']) >= version_tuple(manifest['version']):
                continue
        registry.install(archive, digest)
        if not current:
            registry.set_enabled(manifest['id'], settings.holo_enabled)
