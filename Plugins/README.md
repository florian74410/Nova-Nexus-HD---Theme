# Plugins

Chaque nouveau plugin aura son sous-dossier `Plugins/<id>/manifest.json` avec `id`, `name`, `version` et une liste de `settings` (`key`, `label`, `type`, `default`). Types de réglages : `boolean`, `integer`, `text`. Le noyau v0.1 découvre les manifestes **sans exécuter de code plugin**, puis crée automatiquement une page Paramètres dédiée. Aucun plugin métier activé dans cette version.
