# -*- coding: utf-8 -*-
import os
import time

import xbmc
import xbmcgui

from . import matrix as mx
from . import apo_writer
from . import addon_settings as settings

MEDIA = os.path.join(settings.addon_path(), "resources", "media")

# --- geometria del panel (coordenadas de skin, base 1280x720) ---
PX, PY, PW, PH = 260, 110, 760, 500

ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92

ID_CLOSE = 9001
ID_TOGGLE = 9002


class MixerWindow(xbmcgui.WindowDialog):

    def __init__(self):
        super(MixerWindow, self).__init__()
        self.config_path = settings.get_config_path()
        self.debounce_s = settings.get_debounce_ms() / 1000.0
        self.mode = settings.get_default_mode()

        self.sliders = {}       # key -> ControlSlider
        self.value_labels = {}  # key -> ControlLabel
        self.dynamic_controls = []

        self._closing = False
        self._last_written_key = None
        self._last_change_ts = 0
        self._pending = True  # forzar una primera escritura al abrir

        self._build_static()
        self._build_mode(self.mode)

    # ---------------------------------------------------------- static UI
    def _build_static(self):
        bg = xbmcgui.ControlImage(PX, PY, PW, PH, os.path.join(MEDIA, "panel_bg.png"))
        self.addControl(bg)

        title = xbmcgui.ControlLabel(PX + 20, PY + 12, PW - 40, 30,
                                      "Mezclador de canales (Equalizer APO)",
                                      textColor="0xFFFFFFFF", font="font12_title")
        self.addControl(title)

        self.toggle_btn = xbmcgui.ControlButton(
            PX + PW - 240, PY + 10, 220, 40, "Cambiar a modo Avanzado",
            focusTexture=os.path.join(MEDIA, "button_focus.png"),
            noFocusTexture=os.path.join(MEDIA, "button_bg.png"),
            font="font12")
        self.toggle_btn.setNavigation(self.toggle_btn, self.toggle_btn,
                                       self.toggle_btn, self.toggle_btn)
        self.addControl(self.toggle_btn)
        self.getControlId = None  # placeholder (no usado)

        self.close_btn = xbmcgui.ControlButton(
            PX + 20, PY + PH - 55, 200, 40, "Guardar y cerrar",
            focusTexture=os.path.join(MEDIA, "button_focus.png"),
            noFocusTexture=os.path.join(MEDIA, "button_bg.png"),
            font="font12")
        self.addControl(self.close_btn)

        self.setFocus(self.toggle_btn)

    def _clear_dynamic(self):
        for c in self.dynamic_controls:
            self.removeControl(c)
        self.dynamic_controls = []
        self.sliders = {}
        self.value_labels = {}

    def _build_mode(self, mode):
        self._clear_dynamic()
        self.mode = mode
        if mode == "simple":
            self.toggle_btn.setLabel("Cambiar a modo Avanzado")
            self._build_simple()
        else:
            self.toggle_btn.setLabel("Cambiar a modo Simple")
            self._build_advanced()
        self._pending = True  # recalcular y escribir con el nuevo modo

    # ---------------------------------------------------------- simple mode
    def _build_simple(self):
        order = ["lr", "center", "lfe", "surround"]
        start_y = PY + 90
        row_h = 80
        for i, key in enumerate(order):
            y = start_y + i * row_h
            label = xbmcgui.ControlLabel(PX + 30, y, 300, 30,
                                          mx.SIMPLE_LABELS[key],
                                          textColor="0xFFFFFFFF", font="font12")
            slider = xbmcgui.ControlSlider(
                PX + 340, y + 4, 340, 22,
                textureback=os.path.join(MEDIA, "slider_bg.png"),
                texture=os.path.join(MEDIA, "slider_nib.png"),
                texturefocus=os.path.join(MEDIA, "slider_nib_focus.png"))
            slider.setPercent(50)
            value_lbl = xbmcgui.ControlLabel(PX + 700, y, 50, 30, "50%",
                                              textColor="0xFFAAAAAA", font="font12")
            self.addControl(label)
            self.addControl(slider)
            self.addControl(value_lbl)
            self.dynamic_controls += [label, slider, value_lbl]
            self.sliders[key] = slider
            self.value_labels[key] = value_lbl

        self._wire_navigation(order)

    # ---------------------------------------------------------- advanced mode
    def _build_advanced(self):
        defaults = mx.default_advanced_percents()
        col_defs = [("L", PX + 20, "Contribuyen a L"), ("R", PX + 400, "Contribuyen a R")]
        start_y = PY + 90
        row_h = 62
        order = []

        for out, col_x, header in col_defs:
            hdr = xbmcgui.ControlLabel(col_x, PY + 60, 340, 24, header,
                                        textColor="0xFF66CCFF", font="font12_title")
            self.addControl(hdr)
            self.dynamic_controls.append(hdr)

            for i, ch in enumerate(mx.CHANNELS):
                y = start_y + i * row_h
                key = (out, ch)
                lbl_text = mx.ADVANCED_LABELS[key]
                label = xbmcgui.ControlLabel(col_x, y, 90, 26, lbl_text,
                                              textColor="0xFFFFFFFF", font="font12")
                slider = xbmcgui.ControlSlider(
                    col_x + 95, y + 3, 190, 20,
                    textureback=os.path.join(MEDIA, "slider_bg.png"),
                    texture=os.path.join(MEDIA, "slider_nib.png"),
                    texturefocus=os.path.join(MEDIA, "slider_nib_focus.png"))
                percent = defaults[key]
                slider.setPercent(percent)
                value_lbl = xbmcgui.ControlLabel(col_x + 292, y, 45, 26,
                                                  "%d%%" % percent,
                                                  textColor="0xFFAAAAAA", font="font12")
                self.addControl(label)
                self.addControl(slider)
                self.addControl(value_lbl)
                self.dynamic_controls += [label, slider, value_lbl]
                self.sliders[key] = slider
                self.value_labels[key] = value_lbl
                order.append(key)

        self._wire_navigation(order)

    # ---------------------------------------------------------- navigation
    def _wire_navigation(self, ordered_keys):
        sliders = [self.sliders[k] for k in ordered_keys]
        n = len(sliders)
        for i, s in enumerate(sliders):
            up = sliders[i - 1] if i > 0 else self.toggle_btn
            down = sliders[i + 1] if i < n - 1 else self.close_btn
            s.setNavigation(up, down, self.toggle_btn, self.toggle_btn)
        if sliders:
            self.toggle_btn.setNavigation(self.close_btn, sliders[0], self.toggle_btn, self.toggle_btn)
            self.close_btn.setNavigation(sliders[-1], self.toggle_btn, self.close_btn, self.close_btn)

    # ---------------------------------------------------------- eventos
    def onAction(self, action):
        if action.getId() in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self._closing = True

    def onControl(self, control):
        if control == self.close_btn:
            self._closing = True
        elif control == self.toggle_btn:
            self._build_mode("advanced" if self.mode == "simple" else "simple")

    # ---------------------------------------------------------- calculo/escritura
    def _current_state_key(self):
        return tuple(sorted((k, s.getPercent()) for k, s in self.sliders.items()))

    def _refresh_value_labels(self):
        for key, slider in self.sliders.items():
            self.value_labels[key].setLabel("%d%%" % slider.getPercent())

    def _compute_copy_line(self):
        if self.mode == "simple":
            percents = {k: s.getPercent() for k, s in self.sliders.items()}
            m = mx.build_matrix_from_simple(percents)
        else:
            percents = {k: s.getPercent() for k, s in self.sliders.items()}
            m = mx.build_matrix_from_advanced(percents)
        return mx.matrix_to_copy_line(m)

    def _maybe_write(self):
        key = self._current_state_key()
        now = time.time()
        if key != self._last_written_key:
            self._pending = True
            self._last_change_ts = now

        if self._pending and (now - self._last_change_ts) >= self.debounce_s:
            copy_line = self._compute_copy_line()
            try:
                apo_writer.write_copy_line(self.config_path, copy_line)
            except apo_writer.ApoWriteError as e:
                xbmcgui.Dialog().notification(
                    "Audio Channel Mixer",
                    "No se pudo escribir config.txt: %s" % e,
                    xbmcgui.NOTIFICATION_ERROR, 4000)
            self._last_written_key = key
            self._pending = False

    # ---------------------------------------------------------- bucle principal
    def run(self):
        self.show()
        monitor = xbmc.Monitor()
        while not self._closing and not monitor.abortRequested():
            self._refresh_value_labels()
            self._maybe_write()
            if monitor.waitForAbort(0.1):
                break
        self.close()
