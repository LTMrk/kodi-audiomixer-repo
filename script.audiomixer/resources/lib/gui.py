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
        self.device_pattern = settings.get_device_pattern()
        self.device_key = (self.device_pattern.replace("[", "").replace("]", "")
                            or apo_writer.GLOBAL_KEY)

        self.sliders = {}       # key -> ControlSlider
        self.value_labels = {}  # key -> ControlLabel
        self.dynamic_controls = []

        self._closing = False
        self._last_written_key = None
        self._last_change_ts = 0
        self._pending = True  # forzar una primera escritura al abrir

        # Refleja el estado actual del archivo (si ya hay un bloque guardado
        # para este dispositivo) en vez de arrancar siempre con los valores
        # por defecto. La validez del formato del archivo ya la comprobo
        # main.py antes de crear esta ventana.
        self.mode, self._loaded_percents = self._load_existing_state()

        self._build_static()
        self._build_mode(self.mode)
        self._loaded_percents = None  # solo se aplica en la construccion inicial

    def _load_existing_state(self):
        mode = settings.get_default_mode()
        percents = None
        try:
            body = apo_writer.read_block(self.config_path, self.device_key)
        except apo_writer.ApoFormatError:
            body = None  # ya avisado en main.py; abrimos con los valores por defecto
        if not body:
            return mode, percents

        copy_line = None
        for line in body:
            stripped = line.strip()
            if stripped.startswith("# MODE:"):
                loaded_mode = stripped.split(":", 1)[1].strip().lower()
                if loaded_mode in ("simple", "advanced"):
                    mode = loaded_mode
            elif stripped.lower().startswith("copy:"):
                copy_line = stripped

        if copy_line:
            try:
                matrix = mx.parse_copy_line(copy_line)
                percents = (mx.matrix_to_simple_percents(matrix) if mode == "simple"
                            else mx.matrix_to_advanced_percents(matrix))
            except ValueError:
                percents = None  # Copy: no reconocida: se abre con los valores por defecto

        return mode, percents

    # ---------------------------------------------------------- static UI
    def _build_static(self):
        bg = xbmcgui.ControlImage(PX, PY, PW, PH, os.path.join(MEDIA, "panel_bg.png"))
        self.addControl(bg)

        device_label = self.device_pattern if self.device_pattern else "todos los dispositivos"
        title = xbmcgui.ControlLabel(PX + 20, PY + 12, PW - 40, 30,
                                      "Mezclador de canales - %s" % device_label,
                                      textColor="0xFFFFFFFF", font="font12_title")
        self.addControl(title)

        self.toggle_btn = xbmcgui.ControlButton(
            PX + PW - 240, PY + 10, 220, 40, "Cambiar a modo Avanzado",
            focusTexture=os.path.join(MEDIA, "button_focus.png"),
            noFocusTexture=os.path.join(MEDIA, "button_bg.png"),
            font="font12")
        self.addControl(self.toggle_btn)
        self.toggle_btn.setNavigation(self.toggle_btn, self.toggle_btn,
                                       self.toggle_btn, self.toggle_btn)
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
        loaded = self._loaded_percents or {}
        start_y = PY + 90
        row_h = 80
        for i, key in enumerate(order):
            y = start_y + i * row_h
            percent = loaded.get(key, 50)
            label = xbmcgui.ControlLabel(PX + 30, y, 300, 30,
                                          mx.SIMPLE_LABELS[key],
                                          textColor="0xFFFFFFFF", font="font12")
            slider = xbmcgui.ControlSlider(
                PX + 340, y + 4, 340, 22,
                textureback=os.path.join(MEDIA, "slider_bg.png"))
            value_lbl = xbmcgui.ControlLabel(PX + 700, y, 50, 30, "%d%%" % percent,
                                              textColor="0xFFAAAAAA", font="font12")
            self.addControl(label)
            self.addControl(slider)
            self.addControl(value_lbl)
            slider.setPercent(percent)
            self.dynamic_controls += [label, slider, value_lbl]
            self.sliders[key] = slider
            self.value_labels[key] = value_lbl

        self._wire_navigation(order)

    # ---------------------------------------------------------- advanced mode
    def _build_advanced(self):
        defaults = mx.default_advanced_percents()
        loaded = self._loaded_percents or {}
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
                    textureback=os.path.join(MEDIA, "slider_bg.png"))
                percent = loaded.get(key, defaults[key])
                value_lbl = xbmcgui.ControlLabel(col_x + 292, y, 45, 26,
                                                  "%d%%" % percent,
                                                  textColor="0xFFAAAAAA", font="font12")
                self.addControl(label)
                self.addControl(slider)
                self.addControl(value_lbl)
                slider.setPercent(percent)
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
        percents = {k: s.getPercent() for k, s in self.sliders.items()}
        if self.mode == "simple":
            m = mx.build_matrix_from_simple(percents)
        else:
            m = mx.build_matrix_from_advanced(percents)
        return mx.matrix_to_copy_line(m)

    def _maybe_write(self):
        state_key = self._current_state_key()
        now = time.time()
        if state_key != self._last_written_key:
            self._pending = True
            self._last_change_ts = now

        if self._pending and (now - self._last_change_ts) >= self.debounce_s:
            copy_line = self._compute_copy_line()
            body = ["# MODE: %s" % self.mode]
            if self.device_pattern:
                body.append("Device: %s" % self.device_pattern)
            body.append(copy_line)
            try:
                apo_writer.write_block(self.config_path, self.device_key, body)
            except apo_writer.ApoFormatError as e:
                xbmcgui.Dialog().notification(
                    "Audio Channel Mixer",
                    "config.txt mal formado, no se ha escrito: %s" % e,
                    xbmcgui.NOTIFICATION_ERROR, 5000)
            except apo_writer.ApoWriteError as e:
                xbmcgui.Dialog().notification(
                    "Audio Channel Mixer",
                    "No se pudo escribir config.txt: %s" % e,
                    xbmcgui.NOTIFICATION_ERROR, 4000)
            self._last_written_key = state_key
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
