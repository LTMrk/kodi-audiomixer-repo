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
from resources.lib import keymap_installer

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


def _install_keymap(force):
    # keymap_installer.install(force=True) siempre escribe y devuelve True;
    # con force=False solo escribe (y por tanto solo avisa) si todavia no
    # estaba instalado.
    if keymap_installer.install(force=force):
        xbmcgui.Dialog().notification(
            ADDON_NAME, _L(30021), xbmcgui.NOTIFICATION_INFO, 6000)


def _strip_own_include_line(config_path, local_write_path):
    """Quita (si existe) la linea 'Include: ...' que apunta al archivo de
    respaldo del addon, cuando ya no hace falta porque se esta escribiendo
    directamente en config.txt (opcion A). No toca ninguna otra linea del
    archivo (Peace GUI, etc. quedan intactos). Devuelve True si se quito
    algo."""
    try:
        with open(config_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return False

    needle = local_write_path.lower()
    new_lines = [l for l in lines
                 if not (l.strip().lower().startswith("include:") and needle in l.lower())]
    if len(new_lines) == len(lines):
        return False

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + ("\n" if new_lines else ""))
    except OSError:
        return False
    return True


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
    """Valida el entorno antes de abrir la GUI: SO y donde se va a escribir
    la mezcla. Opcion A (preferida): el config.txt real de Equalizer APO
    directamente. Opcion B (alternativa): un archivo propio del addon en
    addon_data, solo si escribir en el config.txt real falla. Devuelve
    False (tras avisar al usuario) si falta algo imprescindible.
    """
    if platform.system() != "Windows":
        _error("Este complemento solo funciona en Windows, junto con Equalizer APO.\n"
               "El sistema operativo detectado no es Windows.")
        return False

    write_path, using_fallback = settings.resolve_write_path()

    if using_fallback:
        try:
            with open(write_path, "a", encoding="utf-8"):
                pass
        except OSError as e:
            _error("No se puede escribir ni en tu config.txt "
                   "(Ajustes > Ruta de config.txt) ni en el archivo de "
                   "respaldo del addon:\n%s\n\n%s\n\n"
                   "Revisa permisos de escritura o espacio en disco." % (write_path, e))
            return False

    problems = apo_writer.validate(write_path)
    if problems:
        _error("%s\n\n- %s\n\n%s" % (
            _L(30017), "\n- ".join(problems), _L(30018)))
        return False

    if using_fallback and _include_already_configured(write_path) is False:
        xbmcgui.Dialog().ok(
            ADDON_NAME,
            "No se pudo escribir directamente en tu config.txt real, asi "
            "que el addon esta usando un archivo de respaldo propio. Para "
            "que Equalizer APO lo aplique, anade esta linea al FINAL de tu "
            "config.txt real (Ajustes > Ruta de config.txt, o edita el "
            "archivo a mano con el Bloc de notas) y guardala:\n\n%s\n\n"
            "El addon ya esta listo para usarse mientras tanto; el "
            "audio no cambiara hasta que anadas esa linea." % settings.get_include_line())
    elif not using_fallback and not settings.get_keep_existing_config():
        # Opcion A funcionando y el usuario ha pedido limpieza: si quedo
        # una linea "Include:" de una sesion anterior en la que hizo falta
        # la opcion B, ya no sirve de nada -- se quita, sin tocar nada mas
        # del archivo (Peace GUI, etc. se dejan intactos).
        local_path = settings.get_local_write_path()
        if _strip_own_include_line(write_path, local_path):
            xbmcgui.Dialog().notification(
                ADDON_NAME,
                "Se elimino de config.txt una linea Include: que ya no hacia falta.",
                xbmcgui.NOTIFICATION_INFO, 4000)

    return True


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pick_device":
        _pick_device()
    elif len(sys.argv) > 1 and sys.argv[1] == "install_keymap":
        _install_keymap(force=True)
    elif _check_prerequisites():
        _install_keymap(force=False)
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
