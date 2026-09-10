# -*- coding: utf-8 -*-
"""Deteccion, descarga y lanzamiento del instalador oficial de Equalizer
APO, para cuando no esta instalado todavia -- para que el usuario no
tenga que ir a buscarlo el solo. Solo Windows.

Importante: esto NUNCA intenta saltarse ni automatizar UAC de ninguna
forma. Se descarga el instalador oficial de SourceForge (el mismo que
ofrece equalizerapo.com) y se lanza tal cual, sin flags de instalacion
silenciosa -- es Windows quien pide elevacion de permisos y es el propio
asistente de EqualizerAPO quien deja elegir a que dispositivo(s) de
salida instalarlo, exactamente igual que si el usuario lo hubiera
descargado el mismo a mano.

Medidas de seguridad en la descarga (dentro de lo razonable para un
addon sin dependencias externas, sin verificacion de firma de codigo):
- Solo se sigue la redireccion de SourceForge si el host final sigue
  siendo un (sub)dominio de sourceforge.net (los mirrors de SourceForge
  usan subdominios tipo "<mirror>.dl.sourceforge.net") y la descarga es
  por HTTPS.
- Se comprueba que el archivo descargado empiece por la cabecera "MZ" de
  un ejecutable de Windows valido y que su tamano sea razonable (el
  instalador real pesa varios MB) antes de ofrecer lanzarlo.
"""
import os
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request

import xbmc

from . import addon_settings as settings

LOG_TAG = "[script.audiomixer]"


def _log(msg):
    xbmc.log("%s [eqapo_installer] %s" % (LOG_TAG, msg), xbmc.LOGINFO)


# "latest/download" es el mismo enlace que usa el boton de descarga de
# equalizerapo.com; SourceForge redirige desde aqui al mirror mas cercano.
DOWNLOAD_URL = "https://sourceforge.net/projects/equalizerapo/files/latest/download"
ALLOWED_HOST_SUFFIX = "sourceforge.net"
MIN_INSTALLER_SIZE = 300 * 1024  # el instalador real pesa ~12 MB
DEFAULT_INSTALL_ROOT = r"C:\Program Files\EqualizerAPO"
INSTALL_MARKERS = ("Configurator.exe", "EqualizerAPO64.dll", "EqualizerAPO32.dll", "EqualizerAPO.dll")


class DownloadError(Exception):
    pass


def _install_root():
    """Carpeta raiz donde deberia estar instalado Equalizer APO, deducida
    de la ruta de config.txt configurada en Ajustes
    (".../EqualizerAPO/config/config.txt" -> ".../EqualizerAPO"), o la
    ruta por defecto si no hay nada configurado todavia o no encaja con
    ese patron."""
    config_path = settings.get_config_path()
    if config_path:
        config_dir = os.path.dirname(config_path)  # .../EqualizerAPO/config
        root = os.path.dirname(config_dir)  # .../EqualizerAPO
        if root:
            return root
    return DEFAULT_INSTALL_ROOT


def is_installed():
    root = _install_root()
    return any(os.path.isfile(os.path.join(root, marker)) for marker in INSTALL_MARKERS)


def _is_allowed_host(url):
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return host == ALLOWED_HOST_SUFFIX or host.endswith("." + ALLOWED_HOST_SUFFIX)


def download_installer(progress_dialog=None):
    """Descarga el instalador oficial a un archivo temporal y devuelve su
    ruta local. Lanza DownloadError (con un mensaje ya listo para
    mostrar) si la red falla, la redireccion acaba en un host que no es
    de SourceForge, no es HTTPS, el usuario cancela el dialogo de
    progreso, o el archivo resultante no parece un instalador valido."""
    # Sin cabecera User-Agent personalizada a proposito: SourceForge (o un
    # WAF delante) responde 403 a un User-Agent que aparenta ser un
    # navegador sin comportarse como tal (faltan Accept/Accept-Language/
    # etc.), pero acepta sin problema el User-Agent honesto por defecto
    # de urllib -- verificado en la practica antes de fijar esto.
    req = urllib.request.Request(DOWNLOAD_URL)
    try:
        response = urllib.request.urlopen(req, timeout=30)
    except urllib.error.URLError as e:
        raise DownloadError("No se pudo conectar con SourceForge: %s" % e)

    try:
        final_url = response.geturl()
        if not final_url.lower().startswith("https://"):
            raise DownloadError("La descarga no uso HTTPS; cancelada por seguridad.")
        if not _is_allowed_host(final_url):
            raise DownloadError(
                "La descarga redirigio a un host inesperado (%s); cancelada por seguridad."
                % (urllib.parse.urlparse(final_url).hostname or final_url))

        total = int(response.headers.get("Content-Length") or 0)
        fd, tmp_path = tempfile.mkstemp(prefix="EqualizerAPO_", suffix=".exe")
        written = 0
        try:
            with os.fdopen(fd, "wb") as f:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    written += len(chunk)
                    if progress_dialog is not None:
                        percent = int(written * 100 / total) if total else 0
                        progress_dialog.update(
                            percent, "Descargando Equalizer APO... (%d KB)" % (written // 1024))
                        if progress_dialog.iscanceled():
                            raise DownloadError("Descarga cancelada.")
        except Exception:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise
    finally:
        response.close()

    if written < MIN_INSTALLER_SIZE:
        os.remove(tmp_path)
        raise DownloadError(
            "El archivo descargado es demasiado pequeno (%d bytes); puede estar corrupto o "
            "incompleto." % written)
    with open(tmp_path, "rb") as f:
        header = f.read(2)
    if header != b"MZ":
        os.remove(tmp_path)
        raise DownloadError(
            "El archivo descargado no parece un instalador de Windows valido.")

    _log("instalador descargado en %r (%d bytes)" % (tmp_path, written))
    return tmp_path


def launch_installer(installer_path):
    """Lanza el instalador oficial tal cual (sin flags de instalacion
    silenciosa): Windows pedira elevacion de permisos (UAC) por su
    cuenta, y el propio asistente de EqualizerAPO dejara elegir a que
    dispositivo(s) instalarlo. No espera a que termine."""
    _log("lanzando instalador: %r" % installer_path)
    subprocess.Popen([installer_path], shell=False)
