# -*- coding: utf-8 -*-
"""Deteccion de dispositivos de salida de audio en Windows.

Usa WMI (Win32_SoundDevice) via PowerShell, disponible en cualquier Windows
sin dependencias extra. Identifica el adaptador/tarjeta de sonido, no cada
conector por separado (p.ej. "Speakers" vs "Front Panel" del mismo chip no
se distinguen) -- Equalizer APO empareja el patron de "Device:" contra el
texto "Device_name Connection_name GUID", asi que el nombre del adaptador
sigue siendo un patron valido, solo que puede alcanzar a mas de un conector
del mismo chip.
"""
import subprocess

_TIMEOUT_S = 10


def list_playback_devices():
    """Devuelve una lista (sin duplicados, en orden) de nombres de
    dispositivos de sonido detectados, o [] si no se pudo detectar nada
    (PowerShell no disponible, timeout, sistema sin dispositivos, etc.)."""
    try:
        kwargs = {}
        if hasattr(subprocess, "CREATE_NO_WINDOW"):
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command",
             "Get-CimInstance -ClassName Win32_SoundDevice | "
             "Select-Object -ExpandProperty Name"],
            capture_output=True, text=True, timeout=_TIMEOUT_S, **kwargs)
    except Exception:
        return []

    if result.returncode != 0:
        return []

    seen = set()
    devices = []
    for line in result.stdout.splitlines():
        name = line.strip()
        if name and name not in seen:
            seen.add(name)
            devices.append(name)
    return devices
