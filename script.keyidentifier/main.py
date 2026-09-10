# -*- coding: utf-8 -*-
"""Identificador de Teclas/Mando: herramienta de diagnostico independiente
del Audio Channel Mixer, pero que reutiliza exactamente la misma logica de
captura (xbmcgui.Action.getButtonCode() dentro de onAction) que usa
"Detectar pulsando el boton..." alla. Sirve para dos cosas:

1. Ver el id de accion y el codigo real de CUALQUIER tecla o boton de
   mando, sin tener que activar el registro de depuracion ni leer el
   log -- se queda abierta y actualiza en pantalla cada pulsacion, no
   solo la primera.
2. Reproducir en aislado el mismo par de botones enfocables
   (ControlButton + onControl/onClick) que tiene el mezclador, para
   comprobar si "pulsar OK sobre un control con foco" funciona en esta
   instalacion de Kodi -- si aqui tampoco funciona, es un problema de
   Kodi/mando en general, no algo especifico del mezclador.
"""
import os

import xbmc
import xbmcgui

ADDON_NAME = "Identificador de Teclas"
LOG_TAG = "[script.keyidentifier]"
MEDIA = os.path.join(os.path.dirname(__file__), "resources", "media")

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_MOUSE_START = 100
ACTION_MOUSE_END = 109

MAX_HISTORY = 10


def _log(msg):
    xbmc.log("%s %s" % (LOG_TAG, msg), xbmc.LOGINFO)


class KeyIdWindow(xbmcgui.WindowDialog):

    def __init__(self):
        super(KeyIdWindow, self).__init__()
        self._closing = False
        self._history = []
        self._test_clicks = 0

        bg = xbmcgui.ControlImage(140, 60, 1000, 600, os.path.join(MEDIA, "panel_bg.png"))
        self.addControl(bg)

        title = xbmcgui.ControlLabel(
            180, 80, 920, 30, "Identificador de teclas / botones de mando",
            textColor="0xFFFFFFFF", font="font13_title")
        self.addControl(title)

        self.info_label = xbmcgui.ControlLabel(
            180, 130, 920, 70, "Pulsa cualquier tecla o boton del mando...",
            textColor="0xFF66CCFF", font="font12")
        self.addControl(self.info_label)

        self.history_label = xbmcgui.ControlLabel(
            180, 220, 920, 260, "", textColor="0xFFAAAAAA", font="font12")
        self.addControl(self.history_label)

        self.test_btn = xbmcgui.ControlButton(
            180, 530, 460, 40, label="Boton de prueba (navega aqui y pulsa OK)")
        self.addControl(self.test_btn)
        self.test_btn_id = self.test_btn.getId()

        self.close_btn = xbmcgui.ControlButton(180, 585, 200, 40, label="Cerrar")
        self.addControl(self.close_btn)
        self.close_btn_id = self.close_btn.getId()

        self.test_btn.setNavigation(self.close_btn, self.close_btn, self.test_btn, self.test_btn)
        self.close_btn.setNavigation(self.test_btn, self.test_btn, self.close_btn, self.close_btn)

        self.test_result_label = xbmcgui.ControlLabel(
            660, 530, 440, 95,
            "El boton de prueba no se ha activado todavia.",
            textColor="0xFF33CC66", font="font12")
        self.addControl(self.test_result_label)

        self.setFocus(self.test_btn)
        _log("ventana abierta")

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self._closing = True
            return
        if ACTION_MOUSE_START <= action_id <= ACTION_MOUSE_END:
            return  # movimiento/clic de raton (air-mouse en modo puntero): no es "una tecla"
        try:
            button_code = action.getButtonCode()
        except Exception as e:
            _log("action.getButtonCode() lanzo una excepcion: %r" % e)
            button_code = None
        self._record(action_id, button_code)

    def _record(self, action_id, button_code):
        if button_code:
            line = "action id=%d  |  codigo=%d (0x%x)" % (action_id, button_code, button_code)
        elif button_code == 0:
            line = ("action id=%d  |  codigo no disponible (0) -- puede que tu version de "
                     "Kodi sea anterior a la 21 'Omega'" % action_id)
        else:
            line = "action id=%d  |  codigo no disponible (getButtonCode() fallo)" % action_id
        _log("capturado: %s" % line)
        self.info_label.setLabel("Ultima pulsacion:\n%s" % line)
        self._history.insert(0, line)
        del self._history[MAX_HISTORY:]
        self.history_label.setLabel("Historial (mas reciente arriba):\n" + "\n".join(self._history))

    def onControl(self, control):
        _log("onControl control=%r" % control)
        if control == self.close_btn:
            self._closing = True
        elif control == self.test_btn:
            self._register_test_click()

    def onClick(self, controlId):
        _log("onClick controlId=%s (test_btn_id=%s close_btn_id=%s)"
             % (controlId, self.test_btn_id, self.close_btn_id))
        if controlId == self.close_btn_id:
            self._closing = True
        elif controlId == self.test_btn_id:
            self._register_test_click()

    def _register_test_click(self):
        self._test_clicks += 1
        self.test_result_label.setLabel(
            "Boton de prueba activado %d vez/veces.\n\nSi esto NO sube al enfocarlo y pulsar "
            "OK (solo al hacer clic con raton), es el mismo fallo que en el mezclador -- y no "
            "es especifico de ese addon." % self._test_clicks)

    def run(self):
        self.show()
        monitor = xbmc.Monitor()
        while not self._closing and not monitor.abortRequested():
            if monitor.waitForAbort(0.1):
                break
        _log("cerrando")
        self.close()


if __name__ == "__main__":
    window = KeyIdWindow()
    window.run()
    del window
