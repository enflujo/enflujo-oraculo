from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path

from imagen import PantallaSpec, preparar_imagen
from ayudas_serial import mostrar_imagen_async, limpiar_y_dormir
from motores import Motores
from cancion import EM, tocar_cancion_una_vez
from utilidades import aborted

@dataclass
class Ctx:
    puerto_epd: str
    baud: int
    spec: PantallaSpec
    bpm: float
    sleep_epd: bool      # si True, limpia+dormir al final (opt-in)
    modo_prueba: bool
    salida: Path
    difuminado: str
    espera_epd: float = 0.0  # envío a la EPD en paralelo

def run_ciclo(ctx: Ctx, ruta_fuente: Path | None, capturar: bool) -> bool:
    # CAPTURAR/PROCESAR
    if aborted():
        return False
    datos, vista = preparar_imagen(
        ctx.salida, ctx.spec, ctx.difuminado, ruta_fuente, capturar, ctx.modo_prueba
    )
    logging.info(f"[Imagen] Vista previa: {vista}")
    esperado = ((ctx.spec.ancho + 7) // 8) * ctx.spec.alto
    logging.debug(f"[Imagen] Bytes empaquetados: {len(datos)} (esperado {esperado})")

    # MOSTRAR (asíncrono) — se envía mientras suena la canción
    if not aborted():
        th_envio = mostrar_imagen_async(ctx.puerto_epd, ctx.baud, datos, ctx.modo_prueba)
        logging.info("[EPD] Envío de imagen lanzado en segundo plano")
    else:
        return False

    # MUSICA (arranca de inmediato)
    EM.bpm = ctx.bpm
    EM.transposicion = 0
    EM.direccionAlta = False
    with Motores(gpiochip_index="auto", pin_enable=None) as m:
        if aborted():
            logging.info("[Sistema] Abortado antes de iniciar música")
        else:
            logging.info("[Motores] 🎵 Iniciando canción...")
            tocar_cancion_una_vez(m)
            logging.info("[Motores] ✓ Canción terminada")

    # Si hubo abort(), no toques la EPD (ni limpiar ni dormir)
    if aborted():
        logging.info("[Sistema] Abortado: no limpio ni duermo EPD; salgo de inmediato")
        return False

    # FINAL
    if ctx.sleep_epd:
        logging.info("[EPD] Limpio y duermo (flag --sleep activado)")
        limpiar_y_dormir(
            ctx.puerto_epd, ctx.baud, ctx.spec.ancho, ctx.spec.alto,
            dormir=True, modo_prueba=ctx.modo_prueba
        )
    else:
        logging.info("[EPD] Mantengo la imagen; no limpio ni duermo")

    return True
