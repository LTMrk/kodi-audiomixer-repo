# -*- coding: utf-8 -*-
"""Identificador de Teclas/Mando: herramienta de diagnostico independiente
del Audio Channel Mixer, pero que reutiliza exactamente la misma logica de
captura (xbmcgui.Action.getButtonCode() dentro de onAction) que usa
"Detectar pulsando el boton..." alla. Sirve para dos cosas:

1. Ver el id de accion y el codigo real de CUALQUIER tecla o boton de
   mando, sin tener que activar el registro de depuracion ni leer el
   log -- se queda abierta y actualiza en pantalla cada pulsacion, no
   solo la primera.
2. Boton de prueba con el mismo arreglo que ya lleva el mezclador: como
   el clic nativo de Kodi (OnClick/onControl al pulsar OK o hacer clic)
   no llega de forma fiable en algunos entornos, aqui tambien se dispara
   a mano (via onAction) el mismo manejador que usaria un clic nativo --
   sirve de caso minimo para confirmar que ese enfoque funciona, sin el
   resto de complejidad del mezclador de por medio.
"""
import os

import xbmc
import xbmcgui

ADDON_NAME = "Identificador de Teclas"
LOG_TAG = "[script.keyidentifier]"
MEDIA = os.path.join(os.path.dirname(__file__), "resources", "media")

ACTION_SELECT_ITEM = 7
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_MOUSE_LEFT_CLICK = 100
ACTION_MOUSE_DRAG = 106
ACTION_MOUSE_MOVE = 107

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

        test_rect = (180, 530, 460, 40)
        self.test_btn = xbmcgui.ControlButton(
            *test_rect, label="Boton de prueba (navega aqui y pulsa OK, o haz clic)")
        self.addControl(self.test_btn)
        self.test_btn_id = self.test_btn.getId()
        self._test_rect = test_rect

        close_rect = (180, 585, 200, 40)
        self.close_btn = xbmcgui.ControlButton(*close_rect, label="Cerrar")
        self.addControl(self.close_btn)
        self.close_btn_id = self.close_btn.getId()
        self._close_rect = close_rect

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
        if action_id in (ACTION_MOUSE_DRAG, ACTION_MOUSE_MOVE):
            return  # movimiento continuo (air-mouse en modo puntero): no es "una pulsacion"

        try:
            button_code = action.getButtonCode()
        except Exception as e:
            _log("action.getButtonCode() lanzo una excepcion: %r" % e)
            button_code = None
        self._record(action_id, button_code)

        # El clic nativo de Kodi sobre un ControlButton enfocado (OnClick/
        # onControl, tanto al pulsar OK como al hacer clic con raton) no
        # llega de forma fiable en algunos entornos -- se dispara aqui a
        # mano el mismo manejador que usaria un clic nativo: por foco
        # actual si es OK/Intro, o por coordenadas si es un clic de raton.
        if action_id == ACTION_SELECT_ITEM:
            self.onClick(self.getFocusId())
        elif action_id == ACTION_MOUSE_LEFT_CLICK:
            self._handle_mouse_click(action)

    def _handle_mouse_click(self, action):
        try:
            x, y = action.getAmount1(), action.getAmount2()
        except Exception as e:
            _log("no se pudo leer la posicion del clic: %r" % e)
            return
        if self._point_in(x, y, self._test_rect):
            self.onClick(self.test_btn_id)
        elif self._point_in(x, y, self._close_rect):
            self.onClick(self.close_btn_id)

    @staticmethod
    def _point_in(x, y, rect):
        rx, ry, rw, rh = rect
        return rx <= x <= rx + rw and ry <= y <= ry + rh

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
            "Boton de prueba activado %d vez/veces\n(via OK/mando o clic de raton)." % self._test_clicks)

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
