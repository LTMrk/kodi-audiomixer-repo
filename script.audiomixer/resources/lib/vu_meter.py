# -*- coding: utf-8 -*-
"""Vumetro L/R de la salida de audio real (la mezcla final que realmente
suena, DESPUES de que Equalizer APO haga el downmix), capturada por
loopback WASAPI del dispositivo de reproduccion **por defecto** de
Windows.

Solo ctypes (nada de pip): el Python embebido de Kodi no trae pywin32 ni
comtypes instalados, y pedirle al usuario que instale paquetes ahi es
fragil. Todas las llamadas COM se hacen a mano sobre las vtables de
IMMDeviceEnumerator/IMMDevice/IAudioClient/IAudioCaptureClient, que son
interfaces estables de Windows (sin cambios desde Vista).

Limitacion conocida: mide el dispositivo de reproduccion por defecto del
sistema, no necesariamente el dispositivo concreto seleccionado en
Ajustes > Dispositivo de salida si tienes varios configurados con
Equalizer APO -- capturar un dispositivo que no es el por defecto
requeriria enumerar y resolver el endpoint por nombre, no implementado.

Filosofia de errores: cualquier fallo (COM, formato no soportado,
dispositivo ocupado, no hay audio sonando, DLL no disponible...) apaga el
vumetro solo -- get_levels() sigue devolviendo (0.0, 0.0) y el resto del
mezclador sigue funcionando con normalidad."""
import math
import threading
import time
import uuid

try:
    import xbmc

    def _log(msg):
        xbmc.log("[script.audiomixer] [vu_meter] %s" % msg, xbmc.LOGINFO)
except ImportError:
    def _log(msg):
        pass


# --- constantes/GUIDs de la API WASAPI (Windows Core Audio) ---------------
CLSID_MMDEVICEENUMERATOR = "{BCDE0395-E52F-467C-8E3D-C4579291692E}"
IID_IMMDEVICEENUMERATOR = "{A95664D2-9614-4F35-A746-DE8DB63617E6}"
IID_IAUDIOCLIENT = "{1CB9AD4C-DBFA-4C32-B178-C2F568A703B2}"
IID_IAUDIOCAPTURECLIENT = "{C8ADBD64-E71E-48A0-A4DE-185C395CD317}"

CLSCTX_ALL = 23  # INPROC_SERVER | INPROC_HANDLER | LOCAL_SERVER | REMOTE_SERVER
COINIT_MULTITHREADED = 0x0
E_RENDER = 0
E_MULTIMEDIA = 1
AUDCLNT_SHAREMODE_SHARED = 0
AUDCLNT_STREAMFLAGS_LOOPBACK = 0x00020000
AUDCLNT_BUFFERFLAGS_SILENT = 0x2
WAVE_FORMAT_PCM = 0x0001
WAVE_FORMAT_IEEE_FLOAT = 0x0003
WAVE_FORMAT_EXTENSIBLE = 0xFFFE

BUFFER_DURATION_100NS = 2_000_000  # 200 ms
POLL_INTERVAL_S = 0.03
DECAY_PER_SECOND = 6.0  # cuanto "cae" el nivel por segundo sin picos nuevos


def _guid_bytes(guid_str):
    """bytes_le de uuid.UUID coincide exactamente con el layout binario de
    un GUID de Windows -- evita tener que montar Data1/2/3/4 a mano."""
    return uuid.UUID(guid_str).bytes_le


def _decay_factor(dt, decay_per_second=DECAY_PER_SECOND):
    """Factor multiplicativo (0..1) aplicado al nivel previo del vumetro
    tras dt segundos sin un pico nuevo mayor. Extraido como funcion pura
    para poder probarlo sin Windows."""
    return math.exp(-decay_per_second * max(0.0, dt))


def _update_level(previous, new_peak, dt):
    """Ataque instantaneo (salta al pico si es mayor), caida exponencial
    en caso contrario. Funcion pura, testeable sin ctypes/Windows."""
    return max(new_peak, previous * _decay_factor(dt))


class LoopbackMeter(object):
    """Uso: crear la instancia (barato, no toca Windows todavia), llamar a
    start() cuando la ventana este lista para mostrarse, get_levels() en
    cada refresco de UI (devuelve (l, r) en 0.0-1.0, puede pasarse
    ligeramente de 1.0 en picos), y stop() al cerrar la ventana."""

    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._levels = (0.0, 0.0)

    def start(self):
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="AudioMixerVuMeter")
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        t, self._thread = self._thread, None
        if t is not None:
            t.join(timeout=2.0)

    def get_levels(self):
        with self._lock:
            return self._levels

    def _set_levels(self, l, r):
        with self._lock:
            self._levels = (l, r)

    def _run(self):
        try:
            self._capture_loop()
        except Exception as e:
            _log("vumetro desactivado por un error: %r" % e)
        finally:
            self._set_levels(0.0, 0.0)

    # ---------------------------------------------------------- WASAPI
    def _capture_loop(self):
        import ctypes
        from ctypes import wintypes

        ole32 = ctypes.windll.ole32

        class GUID(ctypes.Structure):
            _fields_ = [("data", ctypes.c_ubyte * 16)]

            @classmethod
            def from_str(cls, guid_str):
                g = cls()
                b = _guid_bytes(guid_str)
                for i in range(16):
                    g.data[i] = b[i]
                return g

        class WAVEFORMATEX(ctypes.Structure):
            _fields_ = [
                ("wFormatTag", ctypes.c_ushort),
                ("nChannels", ctypes.c_ushort),
                ("nSamplesPerSec", ctypes.c_uint32),
                ("nAvgBytesPerSec", ctypes.c_uint32),
                ("nBlockAlign", ctypes.c_ushort),
                ("wBitsPerSample", ctypes.c_ushort),
                ("cbSize", ctypes.c_ushort),
            ]

        HRESULT = ctypes.c_long
        LPVOID = ctypes.c_void_p

        def hr_check(hr, what):
            if hr < 0:
                raise OSError("%s fallo: 0x%08x" % (what, hr & 0xFFFFFFFF))

        def com_call(ptr, index, restype, argtypes, *args):
            functype = ctypes.WINFUNCTYPE(restype, LPVOID, *argtypes)
            vtbl = ctypes.cast(ptr, ctypes.POINTER(LPVOID))[0]
            table = ctypes.cast(vtbl, ctypes.POINTER(LPVOID * (index + 1)))[0]
            func = functype(table[index])
            return func(ptr, *args)

        def com_release(ptr):
            if ptr:
                try:
                    com_call(ptr, 2, ctypes.c_ulong, [])
                except Exception:
                    pass

        ole32.CoInitializeEx.restype = HRESULT
        ole32.CoInitializeEx.argtypes = [LPVOID, ctypes.c_uint32]
        ole32.CoUninitialize.restype = None
        ole32.CoCreateInstance.restype = HRESULT
        ole32.CoCreateInstance.argtypes = [
            ctypes.POINTER(GUID), LPVOID, ctypes.c_ulong,
            ctypes.POINTER(GUID), ctypes.POINTER(LPVOID)]
        ole32.CoTaskMemFree.restype = None
        ole32.CoTaskMemFree.argtypes = [LPVOID]

        hr = ole32.CoInitializeEx(None, COINIT_MULTITHREADED)
        if hr < 0:
            raise OSError("CoInitializeEx fallo: 0x%08x" % (hr & 0xFFFFFFFF))

        enumerator = device = audio_client = capture_client = None
        fmt_ptr = None
        try:
            enumerator = LPVOID()
            hr = ole32.CoCreateInstance(
                ctypes.byref(GUID.from_str(CLSID_MMDEVICEENUMERATOR)), None,
                CLSCTX_ALL, ctypes.byref(GUID.from_str(IID_IMMDEVICEENUMERATOR)),
                ctypes.byref(enumerator))
            hr_check(hr, "CoCreateInstance(MMDeviceEnumerator)")

            device = LPVOID()
            hr = com_call(enumerator, 4, HRESULT,
                           [ctypes.c_int, ctypes.c_int, ctypes.POINTER(LPVOID)],
                           E_RENDER, E_MULTIMEDIA, ctypes.byref(device))
            hr_check(hr, "GetDefaultAudioEndpoint")

            audio_client = LPVOID()
            hr = com_call(device, 3, HRESULT,
                           [ctypes.POINTER(GUID), ctypes.c_ulong, LPVOID, ctypes.POINTER(LPVOID)],
                           ctypes.byref(GUID.from_str(IID_IAUDIOCLIENT)), CLSCTX_ALL, None,
                           ctypes.byref(audio_client))
            hr_check(hr, "IMMDevice::Activate(IAudioClient)")

            fmt_ptr = ctypes.POINTER(WAVEFORMATEX)()
            hr = com_call(audio_client, 8, HRESULT,
                           [ctypes.POINTER(ctypes.POINTER(WAVEFORMATEX))],
                           ctypes.byref(fmt_ptr))
            hr_check(hr, "IAudioClient::GetMixFormat")
            fmt = fmt_ptr.contents
            n_channels = max(1, fmt.nChannels)
            is_float = fmt.wFormatTag == WAVE_FORMAT_IEEE_FLOAT or (
                fmt.wFormatTag == WAVE_FORMAT_EXTENSIBLE and fmt.wBitsPerSample == 32)
            bits_per_sample = fmt.wBitsPerSample or 32
            _log("formato detectado: %d canales, %d bits, %s"
                 % (n_channels, bits_per_sample, "float" if is_float else "pcm entero"))

            hr = com_call(audio_client, 3, HRESULT,
                           [ctypes.c_int, ctypes.c_uint32, ctypes.c_longlong,
                            ctypes.c_longlong, ctypes.POINTER(WAVEFORMATEX), LPVOID],
                           AUDCLNT_SHAREMODE_SHARED, AUDCLNT_STREAMFLAGS_LOOPBACK,
                           BUFFER_DURATION_100NS, 0, fmt_ptr, None)
            hr_check(hr, "IAudioClient::Initialize")

            capture_client = LPVOID()
            hr = com_call(audio_client, 14, HRESULT,
                           [ctypes.POINTER(GUID), ctypes.POINTER(LPVOID)],
                           ctypes.byref(GUID.from_str(IID_IAUDIOCAPTURECLIENT)),
                           ctypes.byref(capture_client))
            hr_check(hr, "IAudioClient::GetService(IAudioCaptureClient)")

            hr = com_call(audio_client, 10, HRESULT, [])
            hr_check(hr, "IAudioClient::Start")
            _log("captura de loopback iniciada")

            level_l = level_r = 0.0
            last_ts = time.time()
            try:
                while not self._stop_event.is_set():
                    packet_frames = ctypes.c_uint32()
                    hr = com_call(capture_client, 5, HRESULT,
                                   [ctypes.POINTER(ctypes.c_uint32)],
                                   ctypes.byref(packet_frames))
                    hr_check(hr, "GetNextPacketSize")

                    peak_l = peak_r = 0.0
                    while packet_frames.value > 0:
                        data_ptr = ctypes.POINTER(ctypes.c_byte)()
                        num_frames = ctypes.c_uint32()
                        flags = ctypes.c_uint32()
                        hr = com_call(
                            capture_client, 3, HRESULT,
                            [ctypes.POINTER(ctypes.POINTER(ctypes.c_byte)),
                             ctypes.POINTER(ctypes.c_uint32), ctypes.POINTER(ctypes.c_uint32),
                             LPVOID, LPVOID],
                            ctypes.byref(data_ptr), ctypes.byref(num_frames),
                            ctypes.byref(flags), None, None)
                        hr_check(hr, "GetBuffer")

                        if num_frames.value and not (flags.value & AUDCLNT_BUFFERFLAGS_SILENT):
                            pl, pr = _peak_from_buffer(
                                ctypes, data_ptr, num_frames.value, n_channels,
                                is_float, bits_per_sample)
                            peak_l = max(peak_l, pl)
                            peak_r = max(peak_r, pr)

                        hr = com_call(capture_client, 4, HRESULT,
                                       [ctypes.c_uint32], num_frames.value)
                        hr_check(hr, "ReleaseBuffer")

                        hr = com_call(capture_client, 5, HRESULT,
                                       [ctypes.POINTER(ctypes.c_uint32)],
                                       ctypes.byref(packet_frames))
                        hr_check(hr, "GetNextPacketSize")

                    now = time.time()
                    dt = now - last_ts
                    last_ts = now
                    level_l = _update_level(level_l, peak_l, dt)
                    level_r = _update_level(level_r, peak_r, dt)
                    self._set_levels(level_l, level_r)

                    self._stop_event.wait(POLL_INTERVAL_S)
            finally:
                try:
                    com_call(audio_client, 11, HRESULT, [])  # Stop
                except Exception:
                    pass
        finally:
            if fmt_ptr:
                try:
                    ole32.CoTaskMemFree(fmt_ptr)
                except Exception:
                    pass
            for p in (capture_client, audio_client, device, enumerator):
                com_release(p)
            ole32.CoUninitialize()


def _peak_from_buffer(ctypes, data_ptr, num_frames, n_channels, is_float, bits_per_sample):
    """Pico absoluto (0.0-~1.0) de los canales L (indice 0) y R (indice 1)
    dentro de este bloque de audio. SPEAKER_FRONT_LEFT/RIGHT son siempre
    los dos primeros canales en el orden de Windows, sea cual sea el
    numero total de canales del formato de mezcla del dispositivo."""
    total_samples = num_frames * n_channels
    if is_float:
        arr = ctypes.cast(data_ptr, ctypes.POINTER(ctypes.c_float * total_samples)).contents
        get = lambda i: arr[i]
    elif bits_per_sample == 16:
        arr = ctypes.cast(data_ptr, ctypes.POINTER(ctypes.c_int16 * total_samples)).contents
        get = lambda i: arr[i] / 32768.0
    elif bits_per_sample == 32:
        arr = ctypes.cast(data_ptr, ctypes.POINTER(ctypes.c_int32 * total_samples)).contents
        get = lambda i: arr[i] / 2147483648.0
    else:
        return 0.0, 0.0

    peak_l = peak_r = 0.0
    right_idx = 1 if n_channels > 1 else 0
    for frame in range(num_frames):
        base = frame * n_channels
        v = abs(get(base))
        if v > peak_l:
            peak_l = v
        v = abs(get(base + right_idx))
        if v > peak_r:
            peak_r = v
    return peak_l, peak_r
