"""Explicit release checks and verified, versioned updates; user files are never replaced."""
import hashlib
import json
import os
import platform
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict
from pathlib import Path, PurePosixPath
from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QProgressBar, QApplication
from . import __version__
from .config import Settings
from .profiles import workspace_dir, current_profile
from .install_engine import install_root, payload_executable, self_test, activate

REPO="florian74410/Health-and-Perfs---Navigation-Controler-Bar"
API="https://api.github.com/repos/"+REPO+"/releases/latest"
MAX_DOWNLOAD=300*1024*1024
MAX_EXPANDED=900*1024*1024


def version(value):
    if not isinstance(value,str) or not re.fullmatch(r"v?\d+\.\d+\.\d+",value):
        raise ValueError("Version de publication invalide")
    return tuple(map(int,value.removeprefix("v").split(".")))


def platform_key():
    machine=platform.machine().lower()
    if machine not in ("aarch64", "arm64", "x86_64", "amd64"):
        raise ValueError("Architecture non prise en charge : " + machine)
    arch="arm64" if machine in ("aarch64","arm64") else "x86_64"
    family="windows" if sys.platform=="win32" else "macos" if sys.platform=="darwin" else "linux"
    return family+"-"+arch


def asset_url(url):
    parsed=urllib.parse.urlparse(url)
    prefix="/"+REPO+"/releases/download/"
    if parsed.scheme!="https" or parsed.netloc!="github.com" or not parsed.path.startswith(prefix) or parsed.username or parsed.query:
        raise ValueError("L’asset doit provenir des releases du dépôt officiel")
    return url


def read_url(url, limit=1024*1024):
    request=urllib.request.Request(url,headers={"User-Agent":"Cyber-Nexus-HUD/"+__version__,"Accept":"application/vnd.github+json"})
    with urllib.request.urlopen(request,timeout=30) as response:
        data=response.read(limit+1)
    if len(data)>limit:raise ValueError("Réponse de publication trop volumineuse")
    return data


def check_release(include_prereleases=False):
    try:
        release=json.loads(read_url(API.removesuffix('/latest')+'?per_page=20' if include_prereleases else API))
        if include_prereleases:
            release=next((item for item in release if not item.get('draft')),None)
            if release is None:return None
    except urllib.error.HTTPError as error:
        if error.code==404:return None
        raise
    if release.get("draft") or (release.get("prerelease") and not include_prereleases):return None
    remote=release.get("tag_name","").split("-rc.",1)[0]
    if version(remote)<=version(__version__):return None
    manifest_asset=next((a for a in release.get("assets",[]) if a.get("name")=="novabar-update-manifest.json"),None)
    if not manifest_asset:raise ValueError("Une release existe, mais son manifeste de mise à jour manque")
    manifest=json.loads(read_url(asset_url(manifest_asset["browser_download_url"])))
    if manifest.get("schema_version")!=1 or version(manifest.get("version"))!=version(remote):
        raise ValueError("Le manifeste ne correspond pas à la release")
    asset=manifest.get("platforms",{}).get(platform_key())
    if not isinstance(asset,dict):raise ValueError("Aucun paquet pour l’architecture de cette machine")
    asset_url(asset.get("url",""))
    if not re.fullmatch(r"[a-f0-9]{64}",asset.get("sha256","")):raise ValueError("Empreinte du paquet invalide")
    return {"version":remote.removeprefix("v"),"asset":asset}


def extract_runtime(archive,destination):
    destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=True)
    base=destination.resolve()
    with zipfile.ZipFile(archive) as package:
        infos=package.infolist()
        if len(infos)>10000 or sum(i.file_size for i in infos)>MAX_EXPANDED:
            raise ValueError("Archive trop volumineuse")
        names=set();links=[]
        for item in infos:
            path=PurePosixPath(item.filename)
            raw_name=getattr(item,"orig_filename",item.filename)
            if ("\\" in raw_name or "\x00" in raw_name or not item.filename or path.is_absolute() or ".." in path.parts or "\\" in item.filename
                or ":" in item.filename or path.as_posix().casefold() in names):
                raise ValueError("Chemin de mise à jour interdit")
            names.add(path.as_posix().casefold())
            mode=item.external_attr>>16
            if stat.S_ISLNK(mode):
                if item.file_size>4096:raise ValueError("Lien trop long")
                target=package.read(item).decode("utf-8")
                normalized=posixpath.normpath(posixpath.join(str(path.parent),target))
                if (not target or PurePosixPath(target).is_absolute() or "\\" in target or ":" in target
                    or normalized==".." or normalized.startswith("../") or "\x00" in target):
                    raise ValueError("Lien sortant du paquet")
                links.append((path,target))
        for item in infos:
            if stat.S_ISLNK(item.external_attr>>16):continue
            target=destination.joinpath(*PurePosixPath(item.filename).parts)
            if not target.parent.resolve().is_relative_to(base):raise ValueError("Dossier sortant du paquet")
            if item.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with package.open(item) as src,target.open("wb") as dst:shutil.copyfileobj(src,dst,1024*1024)
            target.chmod(0o755 if (item.external_attr>>16)&0o111 else 0o644)
        # Create links only after all regular files, so no archive write follows a link.
        for path,target in links:
            link=destination.joinpath(*path.parts)
            if not link.parent.resolve().is_relative_to(base):raise ValueError("Parent de lien externe")
            link.parent.mkdir(parents=True,exist_ok=True)
            normalized=posixpath.normpath(posixpath.join(str(path.parent),target))
            destination_path=destination.joinpath(*PurePosixPath(normalized).parts)
            link.symlink_to(target,target_is_directory=destination_path.is_dir())
        for path,target in links:
            link=destination.joinpath(*path.parts)
            try:
                if not link.resolve().is_relative_to(base) or not link.exists():
                    raise ValueError("Cible de lien manquante ou externe")
            except RuntimeError as error:
                raise ValueError("Cycle de liens interdit") from error


def prepare_update(release,progress):
    if version(release["version"])<=version(__version__):raise ValueError("Cette version n’est pas plus récente")
    root=install_root();root.mkdir(parents=True,exist_ok=True)
    target=root/"versions"/release["version"]
    if target.exists():raise ValueError("Cette version est déjà préparée. Le dossier existant n’a pas été remplacé.")
    from .profiles import ensure_workspace
    report=ensure_workspace()/"Reports/update.log"
    with tempfile.TemporaryDirectory(dir=root,prefix=".update-") as temp:
        temp=Path(temp);archive=temp/"runtime.zip"
        url=asset_url(release["asset"]["url"])
        digest=hashlib.sha256();total=0
        progress(10,"Téléchargement de la publication officielle")
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"Cyber-Nexus-HUD"}),timeout=30) as response,archive.open("wb") as output:
            while True:
                chunk=response.read(1024*1024)
                if not chunk:break
                total+=len(chunk)
                if total>MAX_DOWNLOAD:raise ValueError("Téléchargement trop volumineux")
                digest.update(chunk);output.write(chunk)
        if release["asset"].get("size") is not None and total != release["asset"]["size"]:
            raise ValueError("Taille du paquet incorrecte")
        if digest.hexdigest()!=release["asset"]["sha256"]:raise ValueError("L’empreinte SHA-256 ne correspond pas au manifeste")
        progress(45,"Vérification et déploiement dans une nouvelle version")
        stage=temp/"stage";stage.mkdir();extract_runtime(archive,stage)
        executable=payload_executable(stage)
        if not executable:raise ValueError("Exécutable manquant dans la mise à jour")
        progress(70,"Test isolé du nouvel exécutable")
        self_test(executable,report,expected_version=release["version"])
        relative=executable.relative_to(stage);target.parent.mkdir(parents=True,exist_ok=True);stage.rename(target)
    from .update_recovery import backup_user_data
    recovery = backup_user_data(root)
    settings=Settings.load()
    path=workspace_dir()/"App/Profiles"/(current_profile()+".json")
    profile=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"identity":{}}
    current=root/"installation.json"
    state=json.loads(current.read_text(encoding="utf-8")) if current.exists() else {}
    result=activate(target/relative,settings,profile.get("identity",{}),state.get("desktop_shortcut",False),root,
                    release_version=release["version"], recovery_backup=recovery)
    from .install_engine import cleanup_obsolete_runtimes
    removed=cleanup_obsolete_runtimes(root,release["version"],lambda m:progress(95,m))
    if removed:
        progress(97,"Ancien runtime supprimé : "+", ".join(removed))
    progress(100,"Mise à jour testée · redémarrage prêt")
    return result


class UpdateWorker(QThread):
    checked=Signal(object);completed=Signal(dict);failed=Signal(str);progress=Signal(int,str)
    def __init__(self,release=None,parent=None,include_prereleases=False):
        super().__init__(parent);self.release=release;self.include_prereleases=include_prereleases
    def run(self):
        try:
            if self.release:self.completed.emit(prepare_update(self.release,self.progress.emit))
            else:self.checked.emit(check_release(self.include_prereleases))
        except Exception as error:self.failed.emit(str(error))


class UpdateDialog(QDialog):
    def __init__(self,parent=None,auto_upgrade=False):
        super().__init__(parent)
        self.auto_upgrade=auto_upgrade
        from .installer import WIZARD_STYLE
        self.setStyleSheet(WIZARD_STYLE+"QDialog { background: #061224; }")
        self.setWindowTitle("NOVA NEXUS HD · Mises à jour de NovaBar")
        self.setMinimumWidth(560);self.worker=None;self.release=None;self.prepared=None
        box=QVBoxLayout(self);box.setContentsMargins(24,24,24,24);box.setSpacing(18)
        self.label=QLabel("NOVABAR / v"+__version__+"\nVérification explicite des releases du dépôt officiel.")
        self.label.setWordWrap(True);box.addWidget(self.label)
        self.progress=QProgressBar();self.progress.setRange(0,100);box.addWidget(self.progress)
        self.button=QPushButton("Vérifier les mises à jour");self.button.clicked.connect(self.start);box.addWidget(self.button)
        self.rollback_button=QPushButton("Restaurer la version précédente")
        self.rollback_button.clicked.connect(self.restore_previous)
        box.addWidget(self.rollback_button)
        from PySide6.QtWidgets import QCheckBox
        self.preview_channel=QCheckBox("Inclure les préversions de test (choix volontaire)")
        self.preview_channel.toggled.connect(self.change_channel)
        box.addWidget(self.preview_channel)
        note=QLabel("Les profils, thèmes et plugins restent conservés. Aucune adresse e-mail ni mesure matérielle n’est envoyée. La vérification contacte GitHub, qui reçoit les données habituelles d’une connexion réseau.")
        note.setWordWrap(True);box.addWidget(note)
        if self.auto_upgrade:QTimer.singleShot(0,self.start)

    def change_channel(self):
        self.release=None
        self.button.setText("Vérifier les mises à jour")

    def restore_previous(self):
        from .update_recovery import rollback
        try:
            self.prepared = rollback()
            self.button.setText("Redémarrer NovaBar")
            self.label.setText("Version précédente restaurée. Redémarrage prêt.")
        except Exception as error:
            self.failed(str(error))

    def start(self):
        if self.prepared:
            from .system_env import native_env
            env=dict(native_env(),PYINSTALLER_RESET_ENVIRONMENT="1")
            subprocess.Popen([self.prepared["executable"],"--wait-for-pid",str(os.getpid())],stdin=subprocess.DEVNULL,env=env)
            owner=self.parent()
            while owner is not None and not callable(getattr(owner,"quit_app",None)):
                owner=owner.parent()
            if owner is not None:owner.quit_app()
            else:QApplication.instance().quit()
            return
        self.button.setEnabled(False)
        self.preview_channel.setEnabled(False)
        self.rollback_button.setEnabled(False)
        self.worker=UpdateWorker(self.release,self,include_prereleases=self.preview_channel.isChecked())
        self.worker.checked.connect(self.checked);self.worker.completed.connect(self.completed)
        self.worker.failed.connect(self.failed);self.worker.progress.connect(self.status);self.worker.start()

    def status(self,value,text):self.progress.setValue(value);self.label.setText(text)
    def checked(self,release):
        self.worker.wait();self.release=release;self.button.setEnabled(True)
        self.preview_channel.setEnabled(True);self.rollback_button.setEnabled(True)
        self.label.setText("Version "+release["version"]+" disponible. Installer cette mise à jour ?" if release else "Aucune version stable plus récente publiée pour cette installation.")
        self.button.setText("Installer la mise à jour" if release else "Vérifier à nouveau")
        # Installation always requires the user to press the install button.
    def completed(self,state):
        self.worker.wait();self.prepared=state;self.button.setEnabled(True);self.button.setText("Redémarrer NovaBar")
        self.rollback_button.setEnabled(True)
        if self.auto_upgrade:QTimer.singleShot(700,self.start)
    def failed(self,message):
        if self.worker: self.worker.wait()
        self.label.setText(message);self.button.setEnabled(True)
        self.preview_channel.setEnabled(True);self.rollback_button.setEnabled(True)
    def reject(self):
        if self.worker and self.worker.isRunning():
            return
        super().reject()

    def closeEvent(self,event):
        if self.worker and self.worker.isRunning():event.ignore()
        else:super().closeEvent(event)
