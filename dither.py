from __future__ import annotations
from PIL import Image
from dataclasses import dataclass
from typing import Tuple

@dataclass
class EspecificacionPantalla:
    ancho: int = 104
    alto: int = 212
    rotacion: int = 0  # grados: 0, 90, 180, 270
    espejo: bool = False  # espejo horizontal después de rotar


def cargar_y_preparar(ruta: str, pantalla: EspecificacionPantalla, difuminado: str = "floyd") -> Image.Image:
    """
    Carga una imagen, la redimensiona a la pantalla, y la convierte a 1-bit con difuminado.
    Retorna una imagen PIL en modo '1' donde 1=blanco, 0=negro.
    """
    img = Image.open(ruta).convert("L")  # escala de grises
    # Ajusta manteniendo proporción y luego recorta
    img = img.copy()

    # Aplica rotación primero para que el tamaño objetivo tenga la orientación correcta
    if pantalla.rotacion:
        img = img.rotate(pantalla.rotacion, expand=True)
    if pantalla.espejo:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)

    # Redimensiona: recorte centrado para ajustar
    objetivo = (pantalla.ancho, pantalla.alto)
    img = _redimensionar_recorte_centrado(img, objetivo)

    # Difuminado
    if difuminado == "floyd":
        img1 = img.convert("1", dither=Image.FLOYDSTEINBERG)
    elif difuminado == "ninguno":
        img1 = img.point(lambda p: 255 if p > 127 else 0, mode="1")
    elif difuminado == "bayer":
        # Difuminado ordenado mediante cuantización a 2 colores
        img1 = img.convert("P").quantize(colors=2, method=Image.FASTOCTREE).convert("1")
    else:
        img1 = img.convert("1", dither=Image.FLOYDSTEINBERG)
    return img1


def _redimensionar_recorte_centrado(img: Image.Image, objetivo: Tuple[int, int]) -> Image.Image:
    ancho_obj, alto_obj = objetivo
    ancho_img, alto_img = img.size
    
    # En lugar de letterbox (que agrega bordes blancos), usa recorte centrado
    # Calcula escala para LLENAR el objetivo (recorta en lugar de rellenar)
    escala = max(ancho_obj / ancho_img, alto_obj / alto_img)
    nuevo_ancho = max(1, int(ancho_img * escala))
    nuevo_alto = max(1, int(alto_img * escala))
    img_redimensionada = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)
    
    # Recorta al tamaño exacto desde el centro
    desplaz_x = (nuevo_ancho - ancho_obj) // 2
    desplaz_y = (nuevo_alto - alto_obj) // 2
    img_recortada = img_redimensionada.crop((desplaz_x, desplaz_y, 
                                              desplaz_x + ancho_obj, 
                                              desplaz_y + alto_obj))
    return img_recortada


def empaquetar_bn_bit_mas_significativo_primero(img1: Image.Image) -> bytes:
    """
    Empaqueta una imagen PIL de 1-bit (modo '1') en bytes, con el bit más significativo primero por byte,
    de izquierda a derecha, de arriba a abajo para pantallas de tinta electrónica Waveshare.
    
    VERIFICADO desde prueba funcional de convertidor.py:
    - bytes 0x00 = píxeles negros
    - bytes 0xFF = píxeles blancos
    - Esto coincide: bit 0 = negro, bit 1 = blanco
    
    PIL modo '1': 0=negro, 255=blanco
    Empaqueta como: PIL negro (0) → bit 0, PIL blanco (255) → bit 1
    Resultado: 0x00=negro, 0xFF=blanco (NO se necesita inversión)
    """
    if img1.mode != "1":
        raise ValueError("la imagen debe estar en modo '1'")
    ancho, alto = img1.size
    pixeles = img1.load()
    bytes_por_fila = (ancho + 7) // 8
    salida = bytearray(bytes_por_fila * alto)
    indice = 0
    for y in range(alto):
        byte = 0
        pos_bit = 7  # bit más significativo primero
        for x in range(ancho):
            valor = pixeles[x, y]  # En PIL modo '1': 0=negro, 255=blanco
            # bit 0=negro, bit 1=blanco
            valor_bit = 0 if valor == 0 else 1
            byte |= (valor_bit << pos_bit)
            pos_bit -= 1
            if pos_bit < 0:
                salida[indice] = byte
                indice += 1
                byte = 0
                pos_bit = 7
        if pos_bit != 7:
            # vacía parcial - rellena bits restantes con 1s (blanco)
            while pos_bit >= 0:
                byte |= (1 << pos_bit)
                pos_bit -= 1
            salida[indice] = byte
            indice += 1
    return bytes(salida)
