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
    Abre conexión serial y deja DTR/RTS en bajo para evitar resets fantasma en algunos adaptadores.
    Limpia buffers con pequeñas pausas para dar tiempo al firmware.
    """
    ser = serial.Serial(port=puerto, baudrate=baudios, timeout=tiempo_espera)
    # Estabiliza líneas de control (algunos adaptadores pulsan RESET si DTR/RTS cambian)
    try:
        ser.dtr = False
        ser.rts = False
    except Exception:
        pass

    time.sleep(0.30)
    try:
        ser.reset_input_buffer()
        ser.reset_output_buffer()
    except Exception:
        pass
    time.sleep(0.20)
    return ser


def enviar_limpiar(ser: serial.Serial) -> str:
    """Envía comando de limpieza (no recomendado - causa problemas de visualización)."""
    time.sleep(0.1)
    while ser.in_waiting:
        ser.read(ser.in_waiting)
        time.sleep(0.05)
    
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
        time.sleep(0.05)
    
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
    """Envía datos de cuadro. EPD_2IN13D_Display maneja el refresco automáticamente."""
    # Limpia cualquier dato pendiente
    time.sleep(0.1)
    while ser.in_waiting:
        ser.read(ser.in_waiting)
        time.sleep(0.05)
    
    # Envía comando
    ser.write(b'S')
    ser.flush()
    time.sleep(0.2)  # Pequeña pausa para asegurar que el comando se procese
    
    # Envía datos
    ser.write(datos)
    ser.flush()
    
    # Espera confirmación - EPD_2IN13D_Display espera ocupado internamente (~4-5 segundos)
    limite_tiempo = time.time() + 20.0
    while time.time() < limite_tiempo:
        if ser.in_waiting:
            b = ser.read(1)
            if b == b's':
                return 'cuadro-ok'
            # Ignora registros de depuración
        time.sleep(0.01)
    
    return "tiempo-agotado"
