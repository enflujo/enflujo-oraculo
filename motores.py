from __future__ import annotations
import time, logging
from contextlib import AbstractContextManager

try:
    import lgpio  # type: ignore
except Exception:
    lgpio = None

from cancion import F_MIN, F_MAX, PULSE_MIN_US, EM, duracion_ms, midi_a_hz, nota_a_midi

MOTORES = [
    {"dir": 17, "step": 4},   # Motor 1
    {"dir": 24, "step": 23},  # Motor 2
    {"dir": 20, "step": 16},  # Motor 3
    {"dir": 8,  "step": 25},  # Motor 4
    {"dir": 7,  "step": 21},  # Motor 5
]


def _auto_gpiochip_index() -> int:
    if lgpio is None:
        return 0
    for idx in range(8):
        try:
            h = lgpio.gpiochip_open(idx)
            try:
                info = lgpio.gpiochip_get_info(h)
                lines = info[2] if isinstance(info, tuple) else getattr(info, "lines", 0)
                if lines and lines > 0:
                    return idx
            finally:
                lgpio.gpiochip_close(h)
        except Exception:
            continue
    return 0


class Motores(AbstractContextManager):
    def __init__(self, gpiochip_index: int | str = "auto", pin_enable: int | None = None):
        self.gpiochip_index = _auto_gpiochip_index() if gpiochip_index == "auto" else int(gpiochip_index)
        self.pin_enable = pin_enable
        self.handle = None

    # Context manager
    def __enter__(self):
        if lgpio is None:
            logging.warning("[Motores] lgpio no disponible; modo simulación")
            return self
        self.handle = lgpio.gpiochip_open(self.gpiochip_index)
        if self.pin_enable is not None:
            lgpio.gpio_claim_output(self.handle, self.pin_enable)
            lgpio.gpio_write(self.handle, self.pin_enable, 1)  # deshabilitado
        for m in MOTORES:
            lgpio.gpio_claim_output(self.handle, m["step"])
            lgpio.gpio_claim_output(self.handle, m["dir"])
            lgpio.gpio_write(self.handle, m["dir"], 1)
        logging.info(f"[Motores] gpiochip={self.gpiochip_index}")
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self._tone_off()
        except Exception:
            pass
        if lgpio is not None and self.handle is not None:
            try:
                if self.pin_enable is not None:
                    lgpio.gpio_write(self.handle, self.pin_enable, 1)
                for m in MOTORES:
                    lgpio.gpio_write(self.handle, m["step"], 0)
                    lgpio.gpio_write(self.handle, m["dir"], 0)
            finally:
                lgpio.gpiochip_close(self.handle)
                self.handle = None
        logging.info("[Motores] Cerrados y deshabilitados")

    # Bajo nivel
    def _tone_off(self):
        if lgpio is None or self.handle is None:
            return
        for m in MOTORES:
            try:
                lgpio.tx_pulse(self.handle, m["step"], 0, 0, 0, 0)
                lgpio.gpio_write(self.handle, m["step"], 0)
            except Exception:
                pass

    def _tone_on(self, freq_hz: float):
        if lgpio is None or self.handle is None:
            return
        f = max(F_MIN, min(F_MAX, float(freq_hz)))
        half_us = max(PULSE_MIN_US, int(round(1_000_000.0 / (2.0 * f))))
        self._tone_off()
        for m in MOTORES:
            lgpio.tx_pulse(self.handle, m["step"], half_us, half_us, 0, 0)

    def _tocar(self, hz: float, ms: int, dirAlta: bool):
        if ms <= 0:
            self._tone_off(); return
        if lgpio is None or self.handle is None:
            time.sleep(ms/1000.0); return
        for m in MOTORES:
            lgpio.gpio_write(self.handle, m["dir"], 1 if dirAlta else 0)
        if self.pin_enable is not None:
            lgpio.gpio_write(self.handle, self.pin_enable, 0)  # habilitar
        time.sleep(0.001)
        if hz > 0:
            self._tone_on(hz)
        time.sleep(ms/1000.0)
        self._tone_off()
        if self.pin_enable is not None:
            lgpio.gpio_write(self.handle, self.pin_enable, 1)

    # API musical
    def nota(self, n: int, octava: int, figura: int, alt: int = 0) -> None:
        midi = nota_a_midi(n, octava, alt) + EM.transposicion
        hz = midi_a_hz(midi)
        self._tocar(hz, duracion_ms(figura), EM.direccionAlta)
        EM.direccionAlta = not EM.direccionAlta

    def silencio(self, figura: int) -> None:
        self._tocar(0.0, duracion_ms(figura), EM.direccionAlta)
