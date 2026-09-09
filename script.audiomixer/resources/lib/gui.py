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

# xbmcgui.ControlSlider se ha demostrado poco fiable en este build de Kodi:
# el "nib" no respeta el tamano real de sus texturas (se renderiza enorme y
# pixelado pase lo que se le pase como texture/texturefocus), y ademas los
# clics de raton no llegan de forma consistente a onClick/onControl para
# los controles de esta ventana. Por eso cada "slider" de este addon es en
# realidad un ControlButton invisible (solo para foco/navegacion/clic) mas
# una ControlImage que se dibuja a mano como tirador, y el valor (0-100) se
# guarda y se mueve enteramente en Python, sin usar getPercent/setPercent.
NIB_W, NIB_H = 20, 20
SLIDER_STEP = 2  # % que avanza cada pulsacion de izquierda/derecha

ACTION_MOVE_LEFT = 1
ACTION_MOVE_RIGHT = 2
ACTION_PREVIOUS_MENU = 10
ACTION_NAV_BACK = 92
ACTION_MOUSE_LEFT_CLICK = 100


class MixerWindow(xbmcgui.WindowDialog):

    def __init__(self):
        super(MixerWindow, self).__init__()
        # Opcion A (preferida): escribe directamente en el config.txt real
        # de Equalizer APO. Opcion B (alternativa): si eso falla, usa un
        # archivo propio del addon dentro de addon_data, que el config.txt
        # real debe incluir una vez a mano (ver main.py._include_already_configured).
        self.write_path, self.using_fallback = settings.resolve_write_path()
        self.debounce_s = settings.get_debounce_ms() / 1000.0
        self.device_pattern = settings.get_device_pattern()
        self.device_key = (self.device_pattern.replace("[", "").replace("]", "")
                            or apo_writer.GLOBAL_KEY)
        _log("init: write_path=%r using_fallback=%s device_key=%r"
             % (self.write_path, self.using_fallback, self.device_key))

        self.percents = {}       # key -> int 0-100 (unica fuente de verdad)
        self.slider_ids = {}     # control id -> key (para foco/clic)
        self.slider_rects = {}   # key -> (track_x, track_y, track_w, track_h)
        self.nib_images = {}     # key -> ControlImage (tirador, dibujado a mano)
        self.value_labels = {}   # key -> ControlLabel
        self.dynamic_controls = []

        self._closing = False
        self._last_seen_key = None
        self._last_change_ts = 0
        self._pending = True  # forzar una primera escritura al abrir
        self._dirty_visuals = True  # fuerza un primer redibujado de tiradores/etiquetas

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
        title_text = "Mezclador de canales - %s" % device_label
        if self.using_fallback:
            title_text += "  [archivo de respaldo, revisa Include:]"
        title = xbmcgui.ControlLabel(PX + 20, PY + 12, PW - 40, 30, title_text,
                                      textColor="0xFFFFFFFF", font="font12_title")
        self.addControl(title)

        toggle_rect = (PX + PW - 240, PY + 10, 220, 40)
        self.toggle_btn = xbmcgui.ControlButton(
            *toggle_rect, label="Cambiar a modo Avanzado",
            focusTexture=os.path.join(MEDIA, "button_focus.png"),
            noFocusTexture=os.path.join(MEDIA, "button_bg.png"),
            font="font12")
        self.addControl(self.toggle_btn)
        self.toggle_btn_id = self.toggle_btn.getId()
        self._toggle_rect = toggle_rect

        close_rect = (PX + 20, PY + PH - 55, 200, 40)
        self.close_btn = xbmcgui.ControlButton(
            *close_rect, label="Guardar y cerrar",
            focusTexture=os.path.join(MEDIA, "button_focus.png"),
            noFocusTexture=os.path.join(MEDIA, "button_bg.png"),
            font="font12")
        self.addControl(self.close_btn)
        self.close_btn_id = self.close_btn.getId()
        self._close_rect = close_rect
        _log("botones creados: toggle_btn_id=%s close_btn_id=%s"
             % (self.toggle_btn_id, self.close_btn_id))

        self.toggle_btn.setNavigation(self.toggle_btn, self.toggle_btn,
                                       self.toggle_btn, self.toggle_btn)
        self.setFocus(self.toggle_btn)

    def _clear_dynamic(self):
        for c in self.dynamic_controls:
            self.removeControl(c)
        self.dynamic_controls = []
        self.percents = {}
        self.slider_ids = {}
        self.slider_rects = {}
        self.nib_images = {}
        self.value_labels = {}

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
        self._pending = True   # recalcular y escribir con el nuevo modo
        self._dirty_visuals = True

    # ---------------------------------------------------------- construccion de un slider
    def _add_slider_row(self, key, label_x, label_w, label_text, track_x, track_y,
                         track_w, track_h, value_x, value_w, percent):
        nib_y = track_y + (track_h - NIB_H) // 2

        label = xbmcgui.ControlLabel(label_x, track_y - 2, label_w, track_h + 4,
                                      label_text, textColor="0xFFFFFFFF", font="font12")
        # Boton invisible: solo da foco/navegacion/clic sobre toda la pista.
        slider_btn = xbmcgui.ControlButton(
            track_x, track_y, track_w, track_h, label="",
            focusTexture=os.path.join(MEDIA, "transparent.png"),
            noFocusTexture=os.path.join(MEDIA, "transparent.png"))
        nib_img = xbmcgui.ControlImage(
            self._nib_x(track_x, track_w, percent), nib_y, NIB_W, NIB_H,
            os.path.join(MEDIA, "slider_nib.png"))
        value_lbl = xbmcgui.ControlLabel(value_x, track_y - 2, value_w, track_h + 4,
                                          "%d%%" % percent,
                                          textColor="0xFFAAAAAA", font="font12")

        # Fondo de la pista, por debajo del boton/tirador.
        track_bg = xbmcgui.ControlImage(track_x, track_y, track_w, track_h,
                                         os.path.join(MEDIA, "slider_bg.png"))

        self.addControl(track_bg)
        self.addControl(label)
        self.addControl(slider_btn)
        self.addControl(nib_img)
        self.addControl(value_lbl)

        slider_id = slider_btn.getId()
        self.dynamic_controls += [track_bg, label, slider_btn, nib_img, value_lbl]
        self.percents[key] = percent
        self.slider_ids[slider_id] = key
        self.slider_rects[key] = (track_x, track_y, track_w, track_h)
        self.nib_images[key] = nib_img
        self.value_labels[key] = value_lbl
        return slider_btn

    # ---------------------------------------------------------- simple mode
    def _build_simple(self):
        order = ["lr", "center", "lfe", "surround"]
        loaded = self._loaded_percents or {}
        start_y = PY + 90
        row_h = 80
        btns = []
        for i, key in enumerate(order):
            y = start_y + i * row_h
            percent = loaded.get(key, 50)
            btn = self._add_slider_row(
                key, PX + 30, 300, mx.SIMPLE_LABELS[key],
                PX + 340, y + 4, 340, 22, PX + 700, 50, percent)
            btns.append(btn)

        self._wire_navigation(order, btns)

    # ---------------------------------------------------------- advanced mode
    def _build_advanced(self):
        defaults = mx.default_advanced_percents()
        loaded = self._loaded_percents or {}
        col_defs = [("L", PX + 20, "Contribuyen a L"), ("R", PX + 400, "Contribuyen a R")]
        start_y = PY + 90
        row_h = 62
        order = []
        btns = []

        for out, col_x, header in col_defs:
            hdr = xbmcgui.ControlLabel(col_x, PY + 60, 340, 24, header,
                                        textColor="0xFF66CCFF", font="font12_title")
            self.addControl(hdr)
            self.dynamic_controls.append(hdr)

            for i, ch in enumerate(mx.CHANNELS):
                y = start_y + i * row_h
                key = (out, ch)
                percent = loaded.get(key, defaults[key])
                btn = self._add_slider_row(
                    key, col_x, 90, mx.ADVANCED_LABELS[key],
                    col_x + 95, y + 3, 190, 20, col_x + 292, 45, percent)
                order.append(key)
                btns.append(btn)

        self._wire_navigation(order, btns)

    # ---------------------------------------------------------- navigation
    def _wire_navigation(self, ordered_keys, ordered_btns):
        n = len(ordered_btns)
        for i, b in enumerate(ordered_btns):
            up = ordered_btns[i - 1] if i > 0 else self.toggle_btn
            down = ordered_btns[i + 1] if i < n - 1 else self.close_btn
            # Izquierda/derecha se gestionan a mano en onAction (ajustan el
            # valor); aqui se apuntan al propio boton para que Kodi no
            # intente moverle el foco por su cuenta en esa direccion.
            b.setNavigation(up, down, b, b)
        if ordered_btns:
            self.toggle_btn.setNavigation(self.close_btn, ordered_btns[0],
                                           self.toggle_btn, self.toggle_btn)
            self.close_btn.setNavigation(ordered_btns[-1], self.toggle_btn,
                                          self.close_btn, self.close_btn)

    # ---------------------------------------------------------- eventos
    def onAction(self, action):
        action_id = action.getId()
        if action_id not in (ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT):
            _log("onAction id=%s" % action_id)

        if action_id in (ACTION_PREVIOUS_MENU, ACTION_NAV_BACK):
            self._closing = True
        elif action_id == ACTION_MOUSE_LEFT_CLICK:
            self._handle_mouse_click(action)
        elif action_id in (ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT):
            self._handle_keyboard_step(action_id)

    def _focused_slider_key(self):
        return self.slider_ids.get(self.getFocusId())

    def _handle_keyboard_step(self, action_id):
        key = self._focused_slider_key()
        if key is None:
            return  # el foco esta en un boton, no en un slider: nada que hacer
        delta = -SLIDER_STEP if action_id == ACTION_MOVE_LEFT else SLIDER_STEP
        old = self.percents[key]
        new = max(0, min(100, old + delta))
        self.percents[key] = new
        self._dirty_visuals = True
        # Si ya estaba en el limite y se sigue pulsando hacia ese lado, salta
        # el foco al boton de arriba (como "desbordamiento" de navegacion).
        if new == old and new in (0, 100):
            self.setFocus(self.toggle_btn)

    def _handle_mouse_click(self, action):
        # onClick/onControl no llegan de forma fiable con raton en esta
        # ventana; self.getFocusId() tampoco (el mismo clic ha devuelto
        # focos distintos en sesiones distintas). Se comprueban las
        # coordenadas reales del clic contra los rectangulos conocidos de
        # cada control interactivo (botones y sliders).
        try:
            x, y = action.getAmount1(), action.getAmount2()
        except Exception as e:
            _log("no se pudo leer la posicion del clic: %r" % e)
            return

        _log("clic de raton en (%s, %s)" % (x, y))

        if self._point_in(x, y, self._toggle_rect):
            self._toggle_mode()
            return
        if self._point_in(x, y, self._close_rect):
            self._closing = True
            return
        for key, rect in self.slider_rects.items():
            if self._point_in(x, y, rect):
                track_x, _track_y, track_w, _track_h = rect
                percent = int(round((x - track_x) / float(track_w) * 100))
                percent = max(0, min(100, percent))
                self.percents[key] = percent
                self._dirty_visuals = True
                return

        # No cayo en ningun control conocido: como ultimo recurso, prueba
        # con el control que Kodi diga que tiene el foco.
        focus_id = self.getFocusId()
        _log("clic fuera de los rects conocidos, uso el foco=%s" % focus_id)
        self.onClick(focus_id)

    @staticmethod
    def _point_in(x, y, rect):
        rx, ry, rw, rh = rect[0], rect[1], rect[2], rect[3]
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    def _toggle_mode(self):
        _log("_toggle_mode: %s -> %s" % (self.mode, "advanced" if self.mode == "simple" else "simple"))
        self._build_mode("advanced" if self.mode == "simple" else "simple")

    def onControl(self, control):
        # Respaldo por si en algun caso si llega (ver notas en _handle_mouse_click).
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
        return tuple(sorted(self.percents.items()))

    def _refresh_visuals(self):
        if not self._dirty_visuals:
            return
        for key, percent in self.percents.items():
            self.value_labels[key].setLabel("%d%%" % percent)
            track_x, _track_y, track_w, nib_y = self._nib_geom(key)
            self.nib_images[key].setPosition(self._nib_x(track_x, track_w, percent), nib_y)
        self._dirty_visuals = False

    def _nib_geom(self, key):
        track_x, track_y, track_w, track_h = self.slider_rects[key]
        nib_y = track_y + (track_h - NIB_H) // 2
        return track_x, track_y, track_w, nib_y

    def _compute_copy_line(self):
        if self.mode == "simple":
            m = mx.build_matrix_from_simple(self.percents)
        else:
            m = mx.build_matrix_from_advanced(self.percents)
        return mx.matrix_to_copy_line(m)

    def _maybe_write(self):
        state_key = self._current_state_key()
        now = time.time()
        if state_key != self._last_seen_key:
            # Nuevo cambio detectado: reinicia el reloj del debounce. Antes
            # esto se comparaba contra una variable que solo se actualizaba
            # DENTRO del bloque de escritura de mas abajo -- como ese bloque
            # nunca se alcanzaba (el timestamp se reiniciaba en cada tick
            # porque la condicion seguia siendo cierta), el debounce jamas
            # llegaba a cumplirse y no se escribia nunca nada de forma
            # automatica, ni siquiera estando quieto.
            self._last_seen_key = state_key
            self._last_change_ts = now
            self._pending = True

        if self._pending and (now - self._last_change_ts) >= self.debounce_s:
            copy_line = self._compute_copy_line()
            body = ["# MODE: %s" % self.mode]
            if self.device_pattern:
                body.append("Device: %s" % self.device_pattern)
            body.append("Channel: all")
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
            self._refresh_visuals()
            self._maybe_write()
            if monitor.waitForAbort(0.1):
                break
        _log("run(): saliendo del bucle (closing=%s abortRequested=%s)"
             % (self._closing, monitor.abortRequested()))
        self._force_write()
        self.close()
