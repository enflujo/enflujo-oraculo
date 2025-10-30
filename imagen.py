from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple
from dither import EspecificacionPantalla, cargar_y_preparar, empaquetar_bn_bit_mas_significativo_primero

@dataclass
class PantallaSpec:
    ancho: int
    alto: int
    rotacion: int
    espejo: bool


def preparar_imagen(dest_dir: Path, spec: PantallaSpec, difuminado: str, ruta_fuente: Path | None, capturar: bool, modo_prueba: bool) -> Tuple[bytes, Path]:
    dest_dir.mkdir(parents=True, exist_ok=True)

    if ruta_fuente is None and not capturar:
        raise RuntimeError("Proveer --imagen o --capturar")

    if capturar:
        ruta_fuente = dest_dir / "captura.jpg"
        if not modo_prueba:
            from capturar_enviar import capturar_con_rpicam  # import tardío
            capturar_con_rpicam(ruta_fuente, ancho=800, alto=600)

    assert ruta_fuente is not None
    esp = EspecificacionPantalla(ancho=spec.ancho, alto=spec.alto, rotacion=spec.rotacion, espejo=spec.espejo)
    img1 = cargar_y_preparar(str(ruta_fuente), esp, difuminado=difuminado)
    vista = dest_dir / "vista_previa_1bit.png"
    img1.save(vista)
    datos = empaquetar_bn_bit_mas_significativo_primero(img1)
    return datos, vista
