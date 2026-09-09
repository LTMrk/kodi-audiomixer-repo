# -*- coding: utf-8 -*-
"""Instala un atajo de teclado configurable que abre el mezclador desde
cualquier pantalla, incluida la reproduccion de video a pantalla completa
-- Kodi solo carga keymaps desde userdata/keymaps, nunca desde la carpeta
del propio addon, asi que hay que copiarlo ahi (y regenerarlo si el
usuario cambia de tecla)."""
import os
import xbmc
import xbmcvfs

LOG_TAG = "[script.audiomixer]"


def _log(msg):
    xbmc.log("%s [keymap_installer] %s" % (LOG_TAG, msg), xbmc.LOGINFO)


KEYMAP_FILENAME = "script.audiomixer.xml"
DEFAULT_KEY = "f9"

# Teclas ofrecidas en el selector de Ajustes: las de funcion son las mas
# seguras (casi nunca estan ya mapeadas en global), evitando letras que
# Kodi ya usa para navegacion (c/i/o/m...).
AVAILABLE_KEYS = ["f2", "f3", "f4", "f5", "f6", "f7", "f8",
                  "f9", "f10", "f11", "f12"]

# Botones sin nombre de tecla estandar (mandos/dongles USB "air mouse",
# mandos a distancia con teclas multimedia, etc.) aparecen en el log como
# "CInputManager::HandleKey: ... (0xXXXX, obc-NNNNN) pressed ... action is"
# -- el valor DECIMAL del hexadecimal entre parentesis (0xXXXX, NO el
# "obc-NNNNN", que es solo un numero informativo derivado de forma poco
# fiable para scancodes grandes, ver github.com/xbmc/xbmc/issues/16834) es
# lo que hay que usar aqui como "tecla": se detecta por ser puramente
# numerico y se genera <key id="N"> en vez de una etiqueta con nombre.
# main.py._pick_hotkey() ya hace esa conversion hex->decimal por el usuario.
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
    """Genera el XML del keymap para 'key'. Valida contra las dos unicas
    formas que este addon escribe realmente (digitos puros = id decimal
    ya convertido por main.py._pick_hotkey(), o uno de AVAILABLE_KEYS) --
    cualquier otra cosa (p.ej. alguien edito a mano el campo de texto
    "Tecla rapida actual" en Ajustes con un hexadecimal como "f200" en vez
    de usar "Elegir tecla rapida...") se rechaza y se usa DEFAULT_KEY: un
    tag <f200> generado a partir de eso NO es un nombre de tecla valido de
    Kodi (solo "f2".."f12" etc. lo son) y el atajo se quedaria roto en
    silencio sin este resguardo."""
    text = str(key).strip().lower()
    if text.isdigit():
        return KEYMAP_TEMPLATE_RAW.format(key=text)
    if text in AVAILABLE_KEYS:
        return KEYMAP_TEMPLATE_NAMED.format(key=text)
    _log("tecla invalida %r (revisa 'Tecla rapida actual' en Ajustes -- "
         "usa 'Elegir tecla rapida...' en vez de escribir ahi a mano), "
         "usando la de por defecto (%s)" % (key, DEFAULT_KEY))
    return KEYMAP_TEMPLATE_NAMED.format(key=DEFAULT_KEY)


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
    "f9", o el codigo decimal de un boton sin tecla estandar -- ver
    main.py._pick_hotkey()). Devuelve True si se ha escrito el archivo en
    esta llamada."""
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
