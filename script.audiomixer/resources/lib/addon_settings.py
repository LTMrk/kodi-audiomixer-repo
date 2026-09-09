# -*- coding: utf-8 -*-
import xbmcaddon

ADDON = xbmcaddon.Addon()


def get_config_path():
    return ADDON.getSettingString("config_path")


def get_debounce_ms():
    try:
        return int(ADDON.getSettingInt("debounce_ms"))
    except Exception:
        return 180


def get_default_mode():
    # 0 = Simple, 1 = Avanzado
    try:
        return "advanced" if ADDON.getSettingInt("default_mode") == 1 else "simple"
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
