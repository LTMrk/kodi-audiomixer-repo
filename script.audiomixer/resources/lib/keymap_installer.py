# -*- coding: utf-8 -*-
"""Instala un atajo de teclado configurable que abre el mezclador desde
cualquier pantalla, incluida la reproduccion de video a pantalla completa
-- Kodi solo carga keymaps desde userdata/keymaps, nunca desde la carpeta
del propio addon, asi que hay que copiarlo ahi (y regenerarlo si el
usuario cambia de tecla)."""
import os
import xbmc
import xbmcvfs

KEYMAP_FILENAME = "script.audiomixer.xml"
DEFAULT_KEY = "f9"

# Teclas ofrecidas en el selector de Ajustes: las de funcion son las mas
# seguras (casi nunca estan ya mapeadas en global), evitando letras que
# Kodi ya usa para navegacion (c/i/o/m...).
AVAILABLE_KEYS = ["f2", "f3", "f4", "f5", "f6", "f7", "f8",
                  "f9", "f10", "f11", "f12"]

# Botones sin nombre de tecla estandar (mandos/dongles USB "air mouse",
# mandos a distancia con teclas multimedia, etc.) aparecen en el log como
# "Keyboard: scancode: 0x.. ..." seguido de un
# "CInputManager::HandleKey: ... (0x.., obc-NNNNN) pressed ... action is"
# -- ese NNNNN (el numero tras "obc-") se puede usar directamente como
# "tecla" aqui: se detecta por ser puramente numerico y se genera
# <key id="NNNNN"> en vez de una etiqueta con nombre.
KEYMAP_TEMPLATE_NAMED = """<keymap>
    <global>
        <keyboard>
            <{key}>RunScript(script.audiomixer)</{key}>
        </keyboard>
    </global>
</keymap>
"""

KEYMAP_TEMPLATE_RAW = """<keymap>
    <global>
        <keyboard>
            <key id="{key}">RunScript(script.audiomixer)</key>
        </keyboard>
    </global>
</keymap>
"""


def _keymap_xml(key):
    template = KEYMAP_TEMPLATE_RAW if str(key).isdigit() else KEYMAP_TEMPLATE_NAMED
    return template.format(key=key)


def _keymaps_dir():
    d = xbmcvfs.translatePath("special://profile/keymaps/")
    xbmcvfs.mkdirs(d)
    return d


def keymap_path():
    return os.path.join(_keymaps_dir(), KEYMAP_FILENAME)


def is_installed():
    return os.path.isfile(keymap_path())


def install(key, force=False):
    """Instala (o reinstala si force=True, o si la tecla actual del
    archivo no coincide con 'key') el keymap con esa tecla (nombre como
    "f9", o un codigo numerico obc- para botones sin tecla estandar).
    Devuelve True si se ha escrito el archivo en esta llamada."""
    path = keymap_path()
    xml = _keymap_xml(key)
    if not force and os.path.isfile(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                if f.read() == xml:
                    return False
        except OSError:
            pass
    with open(path, "w", encoding="utf-8") as f:
        f.write(xml)
    xbmc.executebuiltin("Action(reloadkeymaps)")
    return True
