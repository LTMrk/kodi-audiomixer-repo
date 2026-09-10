# -*- coding: utf-8 -*-
"""Ventana minima para "aprender" el codigo de un boton de mando/dongle
pulsandolo, en vez de tener que leerlo a mano del log de depuracion y
convertirlo de hexadecimal. Usa xbmcgui.Action.getButtonCode(), que
Kodi entrega al callback onAction() de cualquier Window/WindowDialog con
el mismo valor entero que el interprete de keymaps usa para emparejar
<key id="N">  -- sin pasos intermedios de lectura/conversion manual, y
por tanto sin margen para equivocarse de numero.

Limitacion conocida: action.getButtonCode() no devolvia ningun valor
util (siempre 0) para addons en Python en versiones de Kodi anteriores a
la 21 "Omega" (bug corregido en xbmc/xbmc#23789). En esas versiones esta
funcion no puede usarse y hay que seguir el metodo manual (leer el log y
usar Ajustes > Elegir tecla rapida... > Otra (codigo hexadecimal))."""
import os

import xbmc
import xbmcgui

LOG_TAG = "[script.audiomixer]"


def _log(msg):
    xbmc.log("%s [key_learner] %s" % (LOG_TAG, msg), xbmc.LOGINFO)


ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_MOUSE_START = 100
ACTION_MOUSE_END = 109
ACTION_NONE = 0
TIMEOUT_S = 15


class _LearnWindow(xbmcgui.WindowDialog):

    def __init__(self, message, media_dir):
        super(_LearnWindow, self).__init__()
        bg_path = os.path.join(media_dir, "panel_bg.png")
        if os.path.isfile(bg_path):
            self.addControl(xbmcgui.ControlImage(140, 280, 1000, 160, bg_path))
        self.addControl(xbmcgui.ControlLabel(
            180, 320, 920, 90, message, textColor="0xFFFFFFFF", font="font13"))
        # None = esperando todavia; 0 = boton detectado pero sin codigo
        # util; "CANCELLED" = el usuario salio; int = codigo capturado.
        self.result = None

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self.result = "CANCELLED"
            self.close()
            return
        if action_id == ACTION_NONE or ACTION_MOUSE_START <= action_id <= ACTION_MOUSE_END:
            return  # ruido de movimiento/clic de raton (modo air-mouse): no es "un boton"
        code = action.getButtonCode()
        _log("boton capturado: action_id=%s buttonCode=%s" % (action_id, code))
        self.result = code or 0


def learn_button(media_dir):
    """Muestra la ventana de captura y espera (con limite de tiempo) a que
    el usuario pulse un boton. Devuelve el codigo entero capturado (puede
    ser 0 si Kodi no lo proporciono -- ver limitacion en el docstring del
    modulo), o None si se cancelo o se agoto el tiempo sin pulsar nada."""
    window = _LearnWindow(
        "Pulsa AHORA el boton del mando que quieras usar\ncomo tecla rapida.  "
        "(Atras para cancelar, %ds de margen)" % TIMEOUT_S,
        media_dir)
    window.show()
    monitor = xbmc.Monitor()
    elapsed = 0.0
    while window.result is None and elapsed < TIMEOUT_S and not monitor.abortRequested():
        if monitor.waitForAbort(0.1):
            break
        elapsed += 0.1
    result = window.result
    window.close()
    del window
    return None if result in (None, "CANCELLED") else result
