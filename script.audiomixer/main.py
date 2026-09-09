# -*- coding: utf-8 -*-
import sys
import os
import platform
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "resources", "lib"))

import xbmc
import xbmcgui
from resources.lib import addon_settings as settings
from resources.lib.addon_settings import ADDON
from resources.lib import apo_writer

ADDON_NAME = "Audio Channel Mixer"


def _L(string_id):
    return ADDON.getLocalizedString(string_id)


def _error(message):
    xbmcgui.Dialog().ok(ADDON_NAME, message)


def _pick_device():
    """Detecta dispositivos de audio del sistema y deja elegir uno (o
    "todos/global") para asociarlo al patron 'Device:' de Equalizer APO.
    Invocado desde Ajustes via RunScript(script.audiomixer,pick_device).
    """
    from resources.lib import audio_devices

    devices = audio_devices.list_playback_devices()
    if not devices:
        xbmcgui.Dialog().notification(
            ADDON_NAME, _L(30015), xbmcgui.NOTIFICATION_WARNING, 4000)

    options = [_L(30014)] + devices
    idx = xbmcgui.Dialog().select(_L(30011), options)
    if idx < 0:
        return
    chosen = "" if idx == 0 else devices[idx - 1]
    settings.set_device_pattern(chosen)
    xbmcgui.Dialog().notification(
        ADDON_NAME, "%s: %s" % (_L(30016), chosen or options[0]),
        xbmcgui.NOTIFICATION_INFO, 3000)


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

    problems = apo_writer.validate(path)
    if problems:
        _error("%s\n\n- %s\n\n%s" % (
            _L(30017), "\n- ".join(problems), _L(30018)))
        return False

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pick_device":
        _pick_device()
    elif _check_prerequisites():
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
