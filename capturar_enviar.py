from __future__ import annotations
import argparse
import subprocess
from pathlib import Path

from dither import EspecificacionPantalla, cargar_y_preparar, empaquetar_bn_bit_mas_significativo_primero
from enviar_serial import abrir_serial, enviar_limpiar, enviar_cuadro_bn, enviar_dormir


def capturar_con_rpicam(ruta_salida: Path, ancho: int, alto: int) -> None:
    """Captura foto usando rpicam-still."""
    comando_base = None
    for ejecutable in ["rpicam-still", "libcamera-still"]:
        if subprocess.run(["which", ejecutable], capture_output=True).returncode == 0:
            comando_base = ejecutable
            break
    
    if not comando_base:
        raise RuntimeError("rpicam-still o libcamera-still no encontrado")
    
    comando = [comando_base, "-n", "-o", str(ruta_salida), "-t", "1000",
               "--width", str(ancho), "--height", str(alto), "-q", "95"]
    
    print(f"Capturando con {comando_base}...")
    subprocess.run(comando, check=True)


def principal():
    analizador = argparse.ArgumentParser(description="Captura y muestra fotos en pantalla de tinta electrónica vía ESP32")
    analizador.add_argument("--puerto", help="Puerto serial (ej., /dev/ttyACM0)")
    analizador.add_argument("--imagen", help="Usa imagen existente en lugar de capturar")
    analizador.add_argument("--capturar", action="store_true", help="Captura nueva foto desde la cámara")
    analizador.add_argument("--salida", default="out", help="Directorio de salida (por defecto: out)")
    analizador.add_argument("--difuminado", choices=["floyd", "bayer", "ninguno"], default="floyd",
                    help="Algoritmo de difuminado (por defecto: floyd)")
    analizador.add_argument("--rotacion", type=int, default=0, choices=[0, 90, 180, 270],
                    help="Ángulo de rotación (por defecto: 0)")
    analizador.add_argument("--espejo", action="store_true", help="Espejo horizontal")
    analizador.add_argument("--ancho-pantalla", type=int, default=104, help="Ancho de pantalla (por defecto: 104)")
    analizador.add_argument("--alto-pantalla", type=int, default=212, help="Alto de pantalla (por defecto: 212)")
    analizador.add_argument("--enviar", action="store_true", help="Enviar a pantalla de tinta electrónica")
    analizador.add_argument("--limpiar", action="store_true",
                    help="Limpiar pantalla antes de enviar (NO recomendado - causa problemas)")
    argumentos = analizador.parse_args()

    pantalla = EspecificacionPantalla(ancho=argumentos.ancho_pantalla, alto=argumentos.alto_pantalla, 
                                      rotacion=argumentos.rotacion, espejo=argumentos.espejo)

    directorio_salida = Path(argumentos.salida)
    directorio_salida.mkdir(parents=True, exist_ok=True)

    # Obtiene imagen fuente
    if argumentos.imagen:
        ruta_fuente = Path(argumentos.imagen)
        if not ruta_fuente.exists():
            analizador.error(f"Imagen no encontrada: {ruta_fuente}")
    elif argumentos.capturar:
        ruta_fuente = directorio_salida / "captura.jpg"
        print(f"Capturando foto a {ruta_fuente}...")
        capturar_con_rpicam(ruta_fuente, ancho=800, alto=600)
    else:
        analizador.error("Debe especificar --imagen o --capturar")

    # Procesa imagen
    print(f"Cargando y difuminando {ruta_fuente}...")
    imagen_1bit = cargar_y_preparar(str(ruta_fuente), pantalla, difuminado=argumentos.difuminado)

    # Guarda vista previa y binario
    ruta_vista_previa = directorio_salida / "vista_previa_1bit.png"
    imagen_1bit.save(ruta_vista_previa)
    print(f"Vista previa guardada: {ruta_vista_previa}")

    datos = empaquetar_bn_bit_mas_significativo_primero(imagen_1bit)
    ruta_binario = directorio_salida / "cuadro_bn.bin"
    ruta_binario.write_bytes(datos)
    print(f"Cuadro escrito: {ruta_binario} ({len(datos)} bytes)")

    # Envía a pantalla
    if argumentos.enviar:
        if not argumentos.puerto:
            analizador.error("--enviar requiere --puerto")
        
        print(f"Abriendo serial {argumentos.puerto}...")
        conexion_serial = abrir_serial(argumentos.puerto, 115200)
        try:
            # Limpieza opcional (no recomendado)
            if argumentos.limpiar:
                print("ADVERTENCIA: Limpiar puede causar problemas de visualización")
                print("Limpiando pantalla...")
                print("CONFIRMACIÓN:", enviar_limpiar(conexion_serial))
            
            # Envía cuadro
            print("Enviando cuadro...")
            print("CONFIRMACIÓN:", enviar_cuadro_bn(conexion_serial, datos))
        finally:
            conexion_serial.close()
            print("Serial cerrado.")


if __name__ == "__main__":
    principal()
