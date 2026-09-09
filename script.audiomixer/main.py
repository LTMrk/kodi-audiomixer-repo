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


def _include_already_configured(write_path):
    """Comprueba (mejor esfuerzo, no bloqueante) si el config.txt real del
    usuario ya incluye nuestro archivo local. None = no se pudo comprobar
    (ruta no configurada / archivo no legible); True/False = si se
    encontro o no la referencia."""
    config_path = settings.get_config_path()
    if not config_path or not os.path.isfile(config_path):
        return None
    try:
        with open(config_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        return None
    return write_path.lower() in content.lower()


def _check_prerequisites():
    """Valida el entorno antes de abrir la GUI: SO y el archivo propio del
    addon donde se escribe la mezcla (dentro de addon_data, nunca en
    'Program Files'). Devuelve False (tras avisar al usuario) si falta
    algo imprescindible.
    """
    if platform.system() != "Windows":
        _error("Este complemento solo funciona en Windows, junto con Equalizer APO.\n"
               "El sistema operativo detectado no es Windows.")
        return False

    write_path = settings.get_local_write_path()

    try:
        with open(write_path, "a", encoding="utf-8"):
            pass
    except OSError as e:
        _error("No se puede escribir en:\n%s\n\n%s\n\n"
               "Esta ruta esta dentro de la carpeta de datos del propio "
               "addon, no deberia dar problemas de permisos; revisa el "
               "espacio en disco o los permisos de tu perfil de Kodi." % (write_path, e))
        return False

    problems = apo_writer.validate(write_path)
    if problems:
        _error("%s\n\n- %s\n\n%s" % (
            _L(30017), "\n- ".join(problems), _L(30018)))
        return False

    if _include_already_configured(write_path) is False:
        xbmcgui.Dialog().ok(
            ADDON_NAME,
            "Paso unico de configuracion: para que Equalizer APO aplique la "
            "mezcla, anade esta linea al FINAL de tu config.txt real "
            "(Ajustes > Ruta de config.txt, o edita el archivo a mano con "
            "el Bloc de notas) y guardala:\n\n%s\n\n"
            "El addon ya esta listo para usarse mientras tanto; el "
            "audio no cambiara hasta que anadas esa linea." % settings.get_include_line())

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
