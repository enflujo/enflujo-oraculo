from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import argparse


@dataclass
class Config:
    puerto_epd: str
    baud: int
    pantalla_ancho: int
    pantalla_alto: int
    rotacion: int
    espejo: bool
    bpm: float
    sleep_epd: bool        # << ahora opt-in: solo duerme si es True
    modo_prueba: bool
    salida: Path
    ruta_imagen: Path | None
    capturar: bool
    gpiochip: str | int  # "auto" | 0..7
    pin_enable: int | None
    espera_epd: float


def build_argparser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Foto → EPD → Canción → Limpiar/Sleep")
    ap.add_argument("--puerto", default="/dev/ttyACM0", help="Puerto serial EPD (p.ej. /dev/ttyACM0)")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--imagen", help="Ruta a imagen existente en vez de capturar")
    ap.add_argument("--capturar", action="store_true", help="Capturar con rpicam/libcamera")
    ap.add_argument("--difuminado", choices=["floyd", "bayer", "ninguno"], default="floyd")
    ap.add_argument("--rotacion", type=int, default=0, choices=[0, 90, 180, 270])
    ap.add_argument("--espejo", action="store_true")
    ap.add_argument("--ancho-pantalla", type=int, default=104)
    ap.add_argument("--alto-pantalla", type=int, default=212)
    ap.add_argument("--bpm", type=float, default=70.0, help="Tempo de la canción (default 70)")
    ap.add_argument("--sleep", dest="sleep_epd", action="store_true", help="Dormir la EPD al final (opt-in)")
    ap.add_argument("--salida", default="out", help="Carpeta de salida para capturas y preview")
    ap.add_argument("--modo-prueba", action="store_true", help="Modo prueba: salta serial/GPIO para validar flujo")
    ap.add_argument("--gpiochip", default="auto", help='"auto" o índice 0..7')
    ap.add_argument("--pin-enable", type=int, default=None, help="GPIO opcional para ENABLE de DRV8825")
    ap.add_argument("--espera-epd", type=float, default=3.0, help="Segundos de espera tras enviar imagen")
    return ap


def parse_config() -> tuple[Config, str]:
    ap = build_argparser()
    args = ap.parse_args()

    ruta_imagen = None
    if args.imagen:
        p = Path(args.imagen).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Imagen no encontrada: {p}")
        ruta_imagen = p

    cfg = Config(
        puerto_epd=args.puerto,
        baud=args.baud,
        pantalla_ancho=args.ancho_pantalla,
        pantalla_alto=args.alto_pantalla,
        rotacion=args.rotacion,
        espejo=args.espejo,
        bpm=args.bpm,
        sleep_epd=bool(args.sleep_epd),  # default False → no duerme por defecto
        modo_prueba=args.modo_prueba,
        salida=Path(args.salida),
        ruta_imagen=ruta_imagen,
        capturar=bool(args.capturar and not ruta_imagen),
        gpiochip=args.gpiochip,
        pin_enable=args.pin_enable,
        espera_epd=args.espera_epd,
    )
    return cfg, args.difuminado
