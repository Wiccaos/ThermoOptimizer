# ============================================================
#  Escenario de demostración de OpTemp
# ============================================================
import numpy as np


class SimuladorCarga:
    """
    Genera una curva de carga sintética para demostrar el modelo
    predictivo sin estresar el hardware real durante la presentación.

    Fases del escenario:
        1. Subida gradual  :  5% → 85%  (22 pasos)
        2. Carga sostenida : ~85% con oscilaciones aleatorias (18 pasos)
        3. Enfriamiento    : 85% → 20%  (18 pasos)
        4. Reposo          : ~20% con oscilaciones (12 pasos)
    """

    def __init__(self):
        self._secuencia: np.ndarray = np.array([])
        self.activo: bool = False
        self._paso: int   = 0

    # ── Propiedades ──────────────────────────────────────────

    @property
    def paso_actual(self) -> int:
        return self._paso

    @property
    def total_pasos(self) -> int:
        return len(self._secuencia)

    @property
    def progreso(self) -> float:
        """Porcentaje de avance del escenario (0.0 a 1.0)."""
        if self.total_pasos == 0:
            return 0.0
        return self._paso / self.total_pasos

    # ── Control ──────────────────────────────────────────────

    def iniciar(self) -> None:
        """Genera una nueva secuencia y arranca el simulador."""
        self._secuencia = self._generar_secuencia()
        self._paso      = 0
        self.activo     = True

    def detener(self) -> None:
        """Detiene el simulador y reinicia el estado."""
        self.activo = False
        self._paso  = 0

    def siguiente(self) -> float | None:
        """
        Devuelve el siguiente valor de carga simulada.
        Retorna None cuando la secuencia termina (el llamador
        debe invocar detener() y volver a la lectura real).
        """
        if not self.activo or self._paso >= self.total_pasos:
            self.detener()
            return None

        valor      = float(self._secuencia[self._paso])
        self._paso += 1
        return valor

    # ── Generación de la secuencia ────────────────────────────

    def _generar_secuencia(self) -> np.ndarray:
        subida  = np.linspace(5,  85, 22)
        alta    = 85 + np.random.uniform(-3, 3, 18)
        bajada  = np.linspace(85, 20, 18)
        reposo  = 20 + np.random.uniform(-2, 2, 12)
        return np.concatenate([subida, alta, bajada, reposo])