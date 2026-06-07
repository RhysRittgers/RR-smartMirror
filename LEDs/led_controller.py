import threading
import time
from pi5neo import Pi5Neo, EPixelType

LED_COUNT = 300
SPI_DEVICE = "/dev/spidev0.0"
SPI_SPEED = 800
PIXEL_TYPE = EPixelType.GRBW

_state_lock = threading.Lock()
_current_mode = "off"
_current_color = (0, 0, 0, 0)
_worker_started = False


def _new_strip():
    return Pi5Neo(SPI_DEVICE, LED_COUNT, SPI_SPEED, pixel_type=PIXEL_TYPE)


def _set_all(neo, g, r, b, w):
    for i in range(LED_COUNT):
        neo.set_led_color(i, g, r, b, w)


def _worker():
    neo = _new_strip()

    while True:
        with _state_lock:
            mode = _current_mode
            color = _current_color

        if mode == "off":
            _set_all(neo, 0, 0, 0, 0)

        elif mode == "solid":
            g, r, b, w = color
            _set_all(neo, g, r, b, w)

        elif mode == "party":
            # temporary simple party mode: blue
            _set_all(neo, 0, 0, 255, 0)

        neo.update_strip()


def _ensure_worker_started():
    global _worker_started

    if not _worker_started:
        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        _worker_started = True


def lights_on():
    global _current_mode, _current_color

    _ensure_worker_started()

    with _state_lock:
        _current_mode = "solid"
        _current_color = (0, 0, 0, 255)


def lights_off():
    global _current_mode, _current_color

    _ensure_worker_started()

    with _state_lock:
        _current_mode = "off"
        _current_color = (0, 0, 0, 0)


def vanity():
    global _current_mode, _current_color

    _ensure_worker_started()

    with _state_lock:
        _current_mode = "solid"
        _current_color = (0, 0, 0, 200)


def blue():
    global _current_mode, _current_color

    _ensure_worker_started()

    with _state_lock:
        _current_mode = "solid"
        _current_color = (0, 0, 255, 0)


def custom_color(g: int, r: int, b: int, w: int):
    global _current_mode, _current_color

    _ensure_worker_started()

    with _state_lock:
        _current_mode = "solid"
        _current_color = (g, r, b, w)


def party_mode():
    global _current_mode

    _ensure_worker_started()

    with _state_lock:
        _current_mode = "party"