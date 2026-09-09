# -*- coding: utf-8 -*-
import sys
import os
import platform
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resources", "lib"))

import xbmc
import xbmcgui
from resources.lib import addon_settings as settings

ADDON_NAME = "Audio Channel Mixer"


def _error(message):
    xbmcgui.Dialog().ok(ADDON_NAME, message)


def _check_prerequisites():
    """Valida el entorno antes de abrir la GUI: SO, ajustes y permisos.

    Devuelve False (tras avisar al usuario) si falta algo imprescindible,
    para no dejar que un escenario no ideal termine en una excepcion sin
    explicar (p.ej. sin Equalizer APO instalado, ruta mal configurada o
    sin permisos de escritura sobre esa carpeta).
    """
    if platform.system() != "Windows":
        _error("Este complemento solo funciona en Windows, junto con Equalizer APO.\n"
               "El sistema operativo detectado no es Windows.")
        return False

    path = settings.get_config_path()
    if not path:
        _error("No hay configurada una ruta de config.txt.\n\n"
               "Ve a Ajustes del complemento y establece la ruta al config.txt de "
               "Equalizer APO (por defecto:\n"
               "C:\\Program Files\\EqualizerAPO\\config\\config.txt).")
        return False

    config_dir = os.path.dirname(path)
    if not config_dir or not os.path.isdir(config_dir):
        _error("La carpeta de configuracion no existe:\n%s\n\n"
               "Comprueba que Equalizer APO esta instalado y que la ruta en "
               "Ajustes del complemento es correcta." % config_dir)
        return False

    if not os.path.isfile(path):
        if not xbmcgui.Dialog().yesno(
                ADDON_NAME,
                "No se encontro config.txt en:\n%s\n\n"
                "Puede que Equalizer APO no este instalado o que la ruta "
                "configurada sea incorrecta.\n\n"
                "¿Continuar y crear el archivo de todas formas?" % path):
            return False

    try:
        with open(path, "a", encoding="utf-8"):
            pass
    except OSError as e:
        _error("No se puede escribir en config.txt:\n%s\n\n%s\n\n"
               "Puede que falten permisos de escritura sobre la carpeta de "
               "Equalizer APO: dale permiso de escritura a tu usuario sobre "
               "esa carpeta e intentalo de nuevo." % (path, e))
        return False

    return True


if __name__ == "__main__":
    if _check_prerequisites():
        try:
            from resources.lib.gui import MixerWindow
            window = MixerWindow()
            window.run()
            del window
        except Exception as e:
            xbmc.log("[script.audiomixer] Error inesperado: %s" % traceback.format_exc(),
                      xbmc.LOGERROR)
            _error("Ocurrio un error inesperado al abrir el mezclador:\n%s\n\n"
                   "Revisa el log de Kodi para mas detalles." % e)
