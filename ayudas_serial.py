from __future__ import annotations
import time
import logging
from contextlib import contextmanager
from threading import Thread

from enviar_serial import abrir_serial, enviar_cuadro_bn, enviar_dormir


@contextmanager
def _open_serial_ctx_with_retry(puerto: str, baud: int, intentos: int = 3, pausa_s: float = 0.25):
    """
    Abre el serial con reintentos y asegura cierre al salir del contexto.
    """
    ultimo = None
    ser = None
    for i in range(intentos):
        try:
            ser = abrir_serial(puerto, baud)
            break
        except Exception as e:
            ultimo = e
            logging.warning(f"[EPD] Serial fallo intento {i+1}/{intentos}: {e}")
            time.sleep(pausa_s)
    if ser is None:
        raise RuntimeError(f"No se pudo abrir serial {puerto}: {ultimo}")
    try:
        yield ser
    finally:
        try:
            ser.close()
        except Exception:
            pass


def _despertar_best_effort(puerto: str, baud: int, modo_prueba: bool) -> None:
    """
    Intenta 'despertar' el micro de la EPD si quedó dormido.
    No depende de comandos especiales: envía un newline y espera un instante.
    """
    if modo_prueba:
        return
    try:
        with _open_serial_ctx_with_retry(puerto, baud) as ser:
            try:
                ser.write(b"\n")
                if hasattr(ser, "flush"):
                    ser.flush()
            except Exception:
                pass
            time.sleep(0.2)
    except Exception as e:
        logging.debug(f"[EPD] Despertar best-effort no crítico: {e}")


def mostrar_imagen(puerto: str, baud: int, datos: bytes, modo_prueba: bool) -> None:
    """
    Envío síncrono (bloqueante).
    """
    if modo_prueba:
        logging.info("[EPD] Modo prueba: no envío serial")
        return
    _despertar_best_effort(puerto, baud, modo_prueba)
    with _open_serial_ctx_with_retry(puerto, baud) as ser:
        conf = enviar_cuadro_bn(ser, datos)
        logging.info(f"[EPD] Imagen mostrada ({conf})")


def mostrar_imagen_async(puerto: str, baud: int, datos: bytes, modo_prueba: bool) -> Thread:
    """
    Lanza el envío en un hilo aparte y lo retorna. No bloquea.
    """
    def _send():
        try:
            mostrar_imagen(puerto, baud, datos, modo_prueba)
        except Exception as e:
            logging.error(f"[EPD] Fallo al enviar imagen: {e}")

    th = Thread(target=_send, name="EPDSender", daemon=True)
    th.start()
    return th


def limpiar_y_dormir(puerto: str, baud: int, ancho: int, alto: int, dormir: bool, modo_prueba: bool) -> None:
    if modo_prueba:
        logging.info("[EPD] Modo prueba: no envío limpiar/dormir")
        return
    bytes_por_fila = (ancho + 7) // 8
    total_bytes = bytes_por_fila * alto
    cuadro_blanco = bytes([0xFF] * total_bytes)
    with _open_serial_ctx_with_retry(puerto, baud) as ser:
        conf = enviar_cuadro_bn(ser, cuadro_blanco)
        logging.info(f"[EPD] Limpiar OK ({conf})")
        if dormir:
            conf2 = enviar_dormir(ser)
            logging.info(f"[EPD] Dormir OK ({conf2})")
