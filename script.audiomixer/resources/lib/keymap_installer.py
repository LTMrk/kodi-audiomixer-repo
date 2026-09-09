# -*- coding: utf-8 -*-
"""Instala un atajo de teclado (F9) que abre el mezclador desde cualquier
pantalla, incluida la reproduccion de video a pantalla completa -- Kodi
solo carga keymaps desde userdata/keymaps, nunca desde la carpeta del
propio addon, asi que hay que copiarlo ahi la primera vez."""
import os
import xbmc
import xbmcvfs

KEYMAP_FILENAME = "script.audiomixer.xml"

KEYMAP_XML = """<keymap>
    <global>
        <keyboard>
            <f9>RunScript(script.audiomixer)</f9>
        </keyboard>
    </global>
</keymap>
"""


def _keymaps_dir():
    d = xbmcvfs.translatePath("special://profile/keymaps/")
    xbmcvfs.mkdirs(d)
    return d


def keymap_path():
    return os.path.join(_keymaps_dir(), KEYMAP_FILENAME)


def is_installed():
    return os.path.isfile(keymap_path())


def install(force=False):
    """Instala (o reinstala si force=True) el keymap. Devuelve True si se
    ha escrito el archivo en esta llamada."""
    path = keymap_path()
    if not force and os.path.isfile(path):
        return False
    with open(path, "w", encoding="utf-8") as f:
        f.write(KEYMAP_XML)
    xbmc.executebuiltin("Action(reloadkeymaps)")
    return True
