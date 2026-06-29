# ============================================================
#  modelos.py — Modelamiento matemático de OpTemp
# ============================================================
from config import TEMP_CRITICA, INTERVALO_ACTUALIZACION


class ModeloTermico:
    """
    Encapsula el modelo matemático de disipación térmica basado
    en cálculo diferencial.

    Funciones principales:
        T(x)  = 0.004x² + 0.1x + 35       (temperatura estimada)
        T'(x) = 0.008x + 0.1              (primera derivada — tasa de cambio)

    Donde x = porcentaje de uso del CPU (0 a 100).
    """

    @staticmethod
    def temperatura(carga: float) -> float:
        """
        T(x) = 0.004x² + 0.1x + 35
        Modela la temperatura del microprocesador según su carga.
        """
        return 0.004 * (carga ** 2) + 0.1 * carga + 35

    @staticmethod
    def tasa_de_cambio(carga: float) -> float:
        """
        T'(x) = 0.008x + 0.1
        Primera derivada de T(x): tasa instantánea de incremento
        térmico por cada punto porcentual adicional de carga.
        """
        return 0.008 * carga + 0.1

    @staticmethod
    def frecuencia_optima(temp: float) -> float:
        """
        Frecuencia de reloj sugerida (GHz) para minimizar costo
        energético según la temperatura actual.

        Criterio de la primera derivada: dU/df = 0
        Escala lineal de 4.0 GHz (35 °C) a 2.4 GHz (75 °C).
        """
        freq = 4.0 - (temp - 35) * (1.6 / 40)
        return max(2.4, min(4.0, freq))

    @staticmethod
    def tiempo_al_throttling(temp_actual: float, derivada: float) -> float | None:
        """
        Predice cuántos segundos faltan para alcanzar TEMP_CRITICA
        asumiendo que la tasa de cambio actual se mantiene constante.

        Aproximación lineal (Ley de Newton modificada):
            ΔT = T'(x) · Δt   →   Δt = ΔT / T'(x)

        Retorna None si la temperatura ya superó el umbral o si
        la derivada es nula (sistema estable sin tendencia al alza).
        """
        if temp_actual >= TEMP_CRITICA or derivada <= 0:
            return None
        delta_temp = TEMP_CRITICA - temp_actual
        segundos = (delta_temp / derivada) * (INTERVALO_ACTUALIZACION / 1000)
        return segundos