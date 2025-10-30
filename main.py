from __future__ import annotations
import sys
import logging

from configuracion import parse_config
from imagen import PantallaSpec
from estados import Ctx, run_ciclo
from utilidades import setup_logging, install_sigint_handler


def main():
    cfg, difuminado = parse_config()
    setup_logging(True)
    install_sigint_handler()

    spec = PantallaSpec(
        ancho=cfg.pantalla_ancho,
        alto=cfg.pantalla_alto,
        rotacion=cfg.rotacion,
        espejo=cfg.espejo,
    )

    ctx = Ctx(
        puerto_epd=cfg.puerto_epd,
        baud=cfg.baud,
        spec=spec,
        bpm=cfg.bpm,
        sleep_epd=cfg.sleep_epd,     # << pasa el flag
        modo_prueba=cfg.modo_prueba,
        salida=cfg.salida,
        difuminado=difuminado,
        espera_epd=cfg.espera_epd,
    )

    ruta_fuente = cfg.ruta_imagen
    try:
        ok = run_ciclo(ctx, ruta_fuente, capturar=cfg.capturar)
        if not ok:
            logging.warning("[Sistema] Ciclo abortado")
            sys.exit(2)
    except KeyboardInterrupt:
        logging.warning("[Sistema] Cancelado por usuario")
        sys.exit(130)
    except Exception:
        logging.exception("[Sistema] Error no controlado")
        sys.exit(1)


if __name__ == "__main__":
    main()
