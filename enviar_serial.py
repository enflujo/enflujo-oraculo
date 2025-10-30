from __future__ import annotations
import serial
import time

CONFIRMACIONES = {
    b'c': 'limpieza-ok',
    b's': 'cuadro-ok',
    b'q': 'dormir-ok',
    b'T': 'tiempo-agotado',
    b'E': 'error'
}

def abrir_serial(puerto: str, baudios: int = 115200, tiempo_espera: float = 2.0) -> serial.Serial:
    """
    Apertura simple, sin tocar DTR/RTS (evita resets/bootloader involuntarios).
    Limpia buffers con pequeñas pausas.
    """
    ser = serial.Serial(port=puerto, baudrate=baudios, timeout=tiempo_espera)
    # NO tocar ser.dtr / ser.rts
    time.sleep(1.0)  # tiempo para que el firmware prepare el parser
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception:
        pass
    time.sleep(0.2)
    return ser


def enviar_limpiar(ser: serial.Serial) -> str:
    """Envía comando de limpieza (no recomendado salvo diagnóstico)."""
    time.sleep(0.1)
    while ser.in_waiting:
        ser.read(ser.in_waiting)
        time.sleep(0.02)

    ser.write(b'C')
    ser.flush()

    limite_tiempo = time.time() + 10.0
    while time.time() < limite_tiempo:
        if ser.in_waiting:
            b = ser.read(1)
            if b == b'c':
                return 'limpieza-ok'
        time.sleep(0.01)
    return "tiempo-agotado"


def enviar_dormir(ser: serial.Serial) -> str:
    """Envía comando de dormir."""
    time.sleep(0.1)
    while ser.in_waiting:
        ser.read(ser.in_waiting)
        time.sleep(0.02)

    ser.write(b'Q')
    ser.flush()

    limite_tiempo = time.time() + 5.0
    while time.time() < limite_tiempo:
        if ser.in_waiting:
            b = ser.read(1)
            if b == b'q':
                return 'dormir-ok'
        time.sleep(0.01)
    return "tiempo-agotado"


def enviar_cuadro_bn(ser: serial.Serial, datos: bytes) -> str:
    """
    Envía datos de cuadro. El firmware hace el refresco (toma ~4–6 s).
    Protocolo: 'S' + payload 1-bit (MSB->LSB por byte), sin tamaño explícito.
    """
    # Limpia cualquier eco pendiente
    time.sleep(0.1)
    while ser.in_waiting:
        ser.read(ser.in_waiting)
        time.sleep(0.01)

    # Comando
    ser.write(b'S')
    ser.flush()
    time.sleep(0.3)  # margen para que el firmware entre en modo recepción

    # Datos
    ser.write(datos)
    ser.flush()

    # Confirmación (bloquea hasta 20 s)
    limite_tiempo = time.time() + 20.0
    while time.time() < limite_tiempo:
        if ser.in_waiting:
            b = ser.read(1)
            if b == b's':
                return 'cuadro-ok'
        time.sleep(0.01)

    return "tiempo-agotado"
