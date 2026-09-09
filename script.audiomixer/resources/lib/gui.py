# -*- coding: utf-8 -*-
import os
import time

import xbmc
import xbmcgui

from . import matrix as mx
from . import apo_writer
from . import addon_settings as settings

MEDIA = os.path.join(settings.addon_path(), "resources", "media")

LOG_TAG = "[script.audiomixer]"


def _log(msg):
    xbmc.log("%s %s" % (LOG_TAG, msg), xbmc.LOGINFO)

# --- geometria del panel (coordenadas de skin, base 1280x720) ---
PX, PY, PW, PH = 260, 110, 760, 500

# xbmcgui.ControlSlider ignora el tamano real de las imagenes texture/
# texturefocus y las estira a un tamano propio (en algunos builds de Kodi
# eso da un "nib" enorme y pixelado en vez de un tirador pequeno). Para
# evitarlo, el ControlSlider se usa solo para el foco/lectura de valor con
# un texture/texturefocus transparente, y el tirador visible es una
# ControlImage aparte que se coloca a mano segun el porcentaje actual.
NIB_W, NIB_H = 20, 20

ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_MOUSE_LEFT_CLICK = 100

ID_CLOSE = 9001
ID_TOGGLE = 9002


class MixerWindow(xbmcgui.WindowDialog):

    def __init__(self):
        super(MixerWindow, self).__init__()
        # El bloque del mezclador se lee/escribe siempre en un archivo propio
        # del addon (escribible sin depender de permisos sobre Program
        # Files); el config.txt real de Equalizer APO solo necesita una vez
        # la linea "Include:" que apunta a este archivo (ver main.py).
        self.write_path = settings.get_local_write_path()
        self.debounce_s = settings.get_debounce_ms() / 1000.0
        self.device_pattern = settings.get_device_pattern()
        self.device_key = (self.device_pattern.replace("[", "").replace("]", "")
                            or apo_writer.GLOBAL_KEY)
        _log("init: write_path=%r device_key=%r" % (self.write_path, self.device_key))

        self.sliders = {}       # key -> ControlSlider (foco/valor, tirador invisible)
        self.value_labels = {}  # key -> ControlLabel
        self.nib_images = {}    # key -> ControlImage (tirador visible, dibujado a mano)
        self.track_geom = {}    # key -> (track_x, track_w, nib_y)
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
        _log("estado cargado: mode=%r loaded_percents=%r" % (self.mode, self._loaded_percents))

        self._build_static()
        self._build_mode(self.mode)
        self._loaded_percents = None  # solo se aplica en la construccion inicial

    def _load_existing_state(self):
        mode = settings.get_default_mode()
        percents = None
        try:
            body = apo_writer.read_block(self.write_path, self.device_key)
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
        self.toggle_btn_id = self.toggle_btn.getId()

        self.close_btn = xbmcgui.ControlButton(
            PX + 20, PY + PH - 55, 200, 40, "Guardar y cerrar",
            focusTexture=os.path.join(MEDIA, "button_focus.png"),
            noFocusTexture=os.path.join(MEDIA, "button_bg.png"),
            font="font12")
        self.addControl(self.close_btn)
        self.close_btn_id = self.close_btn.getId()
        _log("botones creados: toggle_btn_id=%s close_btn_id=%s"
             % (self.toggle_btn_id, self.close_btn_id))

        self.setFocus(self.toggle_btn)

    def _clear_dynamic(self):
        for c in self.dynamic_controls:
            self.removeControl(c)
        self.dynamic_controls = []
        self.sliders = {}
        self.value_labels = {}
        self.nib_images = {}
        self.track_geom = {}

    @staticmethod
    def _nib_x(track_x, track_w, percent):
        return track_x + int(round((track_w - NIB_W) * (percent / 100.0)))

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
            track_x, track_y, track_w, track_h = PX + 340, y + 4, 340, 22
            nib_y = track_y + (track_h - NIB_H) // 2
            label = xbmcgui.ControlLabel(PX + 30, y, 300, 30,
                                          mx.SIMPLE_LABELS[key],
                                          textColor="0xFFFFFFFF", font="font12")
            slider = xbmcgui.ControlSlider(
                track_x, track_y, track_w, track_h,
                textureback=os.path.join(MEDIA, "slider_bg.png"),
                texture=os.path.join(MEDIA, "transparent.png"),
                texturefocus=os.path.join(MEDIA, "transparent.png"))
            nib_img = xbmcgui.ControlImage(
                self._nib_x(track_x, track_w, percent), nib_y, NIB_W, NIB_H,
                os.path.join(MEDIA, "slider_nib.png"))
            value_lbl = xbmcgui.ControlLabel(PX + 700, y, 50, 30, "%d%%" % percent,
                                              textColor="0xFFAAAAAA", font="font12")
            self.addControl(label)
            self.addControl(slider)
            self.addControl(nib_img)
            self.addControl(value_lbl)
            slider.setPercent(percent)
            self.dynamic_controls += [label, slider, nib_img, value_lbl]
            self.sliders[key] = slider
            self.nib_images[key] = nib_img
            self.track_geom[key] = (track_x, track_w, nib_y)
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
                track_x, track_y, track_w, track_h = col_x + 95, y + 3, 190, 20
                nib_y = track_y + (track_h - NIB_H) // 2
                lbl_text = mx.ADVANCED_LABELS[key]
                label = xbmcgui.ControlLabel(col_x, y, 90, 26, lbl_text,
                                              textColor="0xFFFFFFFF", font="font12")
                slider = xbmcgui.ControlSlider(
                    track_x, track_y, track_w, track_h,
                    textureback=os.path.join(MEDIA, "slider_bg.png"),
                    texture=os.path.join(MEDIA, "transparent.png"),
                    texturefocus=os.path.join(MEDIA, "transparent.png"))
                percent = loaded.get(key, defaults[key])
                nib_img = xbmcgui.ControlImage(
                    self._nib_x(track_x, track_w, percent), nib_y, NIB_W, NIB_H,
                    os.path.join(MEDIA, "slider_nib.png"))
                value_lbl = xbmcgui.ControlLabel(col_x + 292, y, 45, 26,
                                                  "%d%%" % percent,
                                                  textColor="0xFFAAAAAA", font="font12")
                self.addControl(label)
                self.addControl(slider)
                self.addControl(nib_img)
                self.addControl(value_lbl)
                slider.setPercent(percent)
                self.dynamic_controls += [label, slider, nib_img, value_lbl]
                self.sliders[key] = slider
                self.nib_images[key] = nib_img
                self.track_geom[key] = (track_x, track_w, nib_y)
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
        action_id = action.getId()
        if action_id not in (ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT):
            _log("onAction id=%s" % action_id)
        if action_id in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self._closing = True
        elif action_id == ACTION_MOUSE_LEFT_CLICK:
            # Con raton, onClick/onControl no se estan disparando para los
            # botones de esta ventana (solo llega el ACTION_MOUSE_LEFT_CLICK
            # crudo). En vez de calcular a mano coordenadas de pantalla,
            # se usa el control que Kodi ya tiene enfocado (el hover del
            # raton lo mueve el foco) y se reutiliza onClick con ese id.
            focus_id = self.getFocusId()
            _log("click de raton, control con foco=%s" % focus_id)
            self.onClick(focus_id)

    def _toggle_mode(self):
        _log("_toggle_mode: %s -> %s" % (self.mode, "advanced" if self.mode == "simple" else "simple"))
        self._build_mode("advanced" if self.mode == "simple" else "simple")

    def onControl(self, control):
        # Kodi solo llama a onControl "cuando el control no maneja el
        # mensaje por si mismo"; para ControlButton el evento normalmente
        # llega por onClick(controlId) en su lugar. Se dejan los dos
        # manejadores por seguridad, cada uno cubre casos distintos.
        _log("onControl control=%r" % control)
        if control == self.close_btn:
            self._closing = True
        elif control == self.toggle_btn:
            self._toggle_mode()

    def onClick(self, controlId):
        _log("onClick controlId=%s (close_btn_id=%s toggle_btn_id=%s)"
             % (controlId, self.close_btn_id, self.toggle_btn_id))
        if controlId == self.close_btn_id:
            self._closing = True
        elif controlId == self.toggle_btn_id:
            self._toggle_mode()

    # ---------------------------------------------------------- calculo/escritura
    def _current_state_key(self):
        return tuple(sorted((k, s.getPercent()) for k, s in self.sliders.items()))

    def _refresh_value_labels(self):
        for key, slider in self.sliders.items():
            percent = slider.getPercent()
            self.value_labels[key].setLabel("%d%%" % percent)
            track_x, track_w, nib_y = self.track_geom[key]
            self.nib_images[key].setPosition(self._nib_x(track_x, track_w, percent), nib_y)

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
            _log("escribiendo bloque device_key=%r en %r: %r"
                 % (self.device_key, self.write_path, body))
            try:
                apo_writer.write_block(self.write_path, self.device_key, body)
                _log("escritura OK")
            except apo_writer.ApoFormatError as e:
                _log("ApoFormatError al escribir: %s" % e)
                xbmcgui.Dialog().notification(
                    "Audio Channel Mixer",
                    "config.txt mal formado, no se ha escrito: %s" % e,
                    xbmcgui.NOTIFICATION_ERROR, 5000)
            except apo_writer.ApoWriteError as e:
                _log("ApoWriteError al escribir: %s" % e)
                xbmcgui.Dialog().notification(
                    "Audio Channel Mixer",
                    "No se pudo escribir config.txt: %s" % e,
                    xbmcgui.NOTIFICATION_ERROR, 4000)
            except Exception as e:
                _log("EXCEPCION NO ESPERADA al escribir: %r" % e)
                raise
            self._last_written_key = state_key
            self._pending = False

    def _force_write(self):
        """Escritura inmediata sin esperar al debounce, para garantizar que
        el ultimo cambio quede guardado sin importar como se cierre la
        ventana (boton, Atras, o salir justo tras mover un slider)."""
        self._pending = True
        self._last_change_ts = 0
        self._maybe_write()

    # ---------------------------------------------------------- bucle principal
    def run(self):
        _log("run(): entrando al bucle principal")
        self.show()
        monitor = xbmc.Monitor()
        while not self._closing and not monitor.abortRequested():
            self._refresh_value_labels()
            self._maybe_write()
            if monitor.waitForAbort(0.1):
                break
        _log("run(): saliendo del bucle (closing=%s abortRequested=%s)"
             % (self._closing, monitor.abortRequested()))
        self._force_write()
        self.close()
