# -*- coding: utf-8 -*-
import os
import xbmcaddon
import xbmcvfs

ADDON = xbmcaddon.Addon()

LOCAL_FILENAME = "kodi_audiomixer.txt"


def get_config_path():
    return ADDON.getSettingString("config_path")


def get_local_write_path():
    """Ruta de un archivo propio del addon (dentro de addon_data, en el
    perfil de Kodi) donde SIEMPRE se puede escribir sin depender de
    permisos sobre 'C:\\Program Files\\...'. El config.txt real de
    Equalizer APO debe incluirlo una vez a mano con una linea
    'Include: "<esta ruta>"' -- ver get_include_line()."""
    profile_dir = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))
    xbmcvfs.mkdirs(profile_dir)
    return os.path.join(profile_dir, LOCAL_FILENAME)


def get_include_line():
    return 'Include: "%s"' % get_local_write_path()


def resolve_write_path():
    """Decide donde escribir el bloque del mezclador esta sesion.

    Opcion A (preferida): el config.txt real de Equalizer APO directamente,
    si se puede escribir ahi. Opcion B (alternativa): el archivo propio del
    addon dentro de addon_data, solo si escribir en el config.txt real
    falla (algunos sistemas restringen la escritura en 'Program Files' de
    forma poco clara). Devuelve (path, es_alternativa: bool)."""
    config_path = get_config_path()
    if config_path:
        try:
            with open(config_path, "a", encoding="utf-8"):
                pass
            return config_path, False
        except OSError:
            pass
    return get_local_write_path(), True


def get_debounce_ms():
    try:
        return int(ADDON.getSettingInt("debounce_ms"))
    except Exception:
        return 180


def get_default_mode():
    # labelenum guarda el texto elegido ("Simple"/"Avanzado"), no un indice.
    try:
        return "advanced" if ADDON.getSettingString("default_mode") == "Avanzado" else "simple"
    except Exception:
        return "simple"


def addon_path():
    return ADDON.getAddonInfo("path")


def get_device_pattern():
    """Patron de dispositivo (Equalizer APO 'Device:') elegido en Ajustes,
    o "" si el usuario quiere el mezclador global (todos los dispositivos)."""
    return (ADDON.getSettingString("device_pattern") or "").strip()


def set_device_pattern(pattern):
    ADDON.setSettingString("device_pattern", pattern or "")
