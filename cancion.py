# Notas / figuras y utilidades musicales
DO, RE, MI, FA, SOL, LA, SI = 0, 2, 4, 5, 7, 9, 11
NATURAL, SOSTENIDO, BEMOL = 0, +1, -1
(
    REDONDA, BLANCA, NEGRA, CORCHEA, SEMICORCHEA, FUSA, SEMIFUSA,
    P_REDONDA, P_BLANCA, P_NEGRA, P_CORCHEA,
    T_NEGRA, T_CORCHEA, T_SEMICORCHEA,
) = range(14)

class EstadoMusical:
    def __init__(self) -> None:
        self.bpm = 120.0
        self.transposicion = 0
        self.direccionAlta = False

EM = EstadoMusical()

F_MIN, F_MAX = 30.0, 3000.0
PULSE_MIN_US = 3


def duracion_ms(figura: int) -> int:
    negra = 60000.0 / EM.bpm
    factor = {
        REDONDA: 4, BLANCA: 2, NEGRA: 1, CORCHEA: 0.5,
        SEMICORCHEA: 0.25, FUSA: 0.125, SEMIFUSA: 0.0625,
        P_REDONDA: 6, P_BLANCA: 3, P_NEGRA: 1.5, P_CORCHEA: 0.75,
        T_NEGRA: (2/3), T_CORCHEA: (1/3), T_SEMICORCHEA: (0.5/3),
    }.get(figura, 1)
    return int(negra * factor)


def midi_a_hz(m: int) -> float:
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


def nota_a_midi(n: int, octava: int, alt: int = NATURAL) -> int:
    return 12 * (octava + 1) + (int(n) + int(alt))

# Partitura (un pase)
_alternarDireccion = False

def tocar_cancion_una_vez(m) -> None:
    global _alternarDireccion
    # PRIMERA FRASE
    m.nota(RE, 4, P_NEGRA); m.silencio(T_CORCHEA)
    m.nota(FA, 4, T_CORCHEA); m.nota(LA, 4, T_CORCHEA)
    m.nota(RE, 4, T_CORCHEA); m.nota(FA, 4, T_CORCHEA); m.nota(LA, 4, T_CORCHEA)
    m.nota(RE, 4, BLANCA); m.silencio(T_CORCHEA)

    m.nota(FA, 4, T_CORCHEA); m.nota(LA, 4, T_CORCHEA)
    m.nota(RE, 4, T_CORCHEA); m.nota(FA, 4, T_CORCHEA)
    m.nota(LA, 4, CORCHEA); m.nota(RE, 4, BLANCA); m.silencio(T_CORCHEA)

    m.nota(SOL, 4, T_CORCHEA); m.nota(FA, 4, T_CORCHEA)
    m.nota(SOL, 4, T_CORCHEA); m.nota(FA, 4, CORCHEA)
    m.nota(RE, 4, REDONDA); m.silencio(T_CORCHEA)

    # SEGUNDA FRASE
    m.nota(FA, 4, T_CORCHEA, SOSTENIDO); m.nota(LA, 4, T_CORCHEA)
    m.nota(RE, 5, T_CORCHEA); m.nota(FA, 4, T_CORCHEA, SOSTENIDO)
    m.nota(LA, 4, T_CORCHEA); m.nota(RE, 5, T_CORCHEA)
    m.nota(SOL, 4, NEGRA); m.silencio(T_CORCHEA)

    m.nota(SI, 4, P_CORCHEA, BEMOL); m.nota(RE, 5, CORCHEA)
    m.nota(SI, 4, CORCHEA, BEMOL); m.nota(SOL, 4, P_CORCHEA)
    m.nota(RE, 5, T_CORCHEA); m.nota(SI, 4, CORCHEA, BEMOL)
    m.nota(SOL, 4, T_NEGRA); m.nota(MI, 4, BLANCA); m.silencio(T_CORCHEA)

    m.nota(SOL, 4, T_CORCHEA); m.nota(DO, 5, T_CORCHEA)
    m.nota(MI, 4, T_CORCHEA); m.nota(SOL, 4, T_CORCHEA)
    m.nota(DO, 5, T_CORCHEA); m.nota(FA, 4, BLANCA); m.silencio(T_CORCHEA)

    m.nota(RE, 4, SEMICORCHEA); m.nota(FA, 4, SEMICORCHEA)
    m.nota(LA, 4, SEMICORCHEA); m.nota(RE, 5, SEMICORCHEA)
    m.nota(DO, 4, CORCHEA); m.nota(SI, 4, SEMICORCHEA, BEMOL)
    m.nota(LA, 4, CORCHEA); m.nota(SOL, 4, CORCHEA)
