# ============================================================
#  Constantes globales de OpTemp
# ============================================================

# Tiempos
INTERVALO_ACTUALIZACION = 1500   # ms entre ciclos de predicción

# Umbrales térmicos
TEMP_CRITICA           = 70.0    # °C — límite de throttling
TEMP_WARN              = 55.0    # °C — advertencia temprana

# Umbrales de derivada T'(x)
UMBRAL_ALERTA_DERIVADA = 0.65    # °C/% — tasa crítica
UMBRAL_WARN_DERIVADA   = 0.45    # °C/% — tasa de advertencia

# ── Paleta de colores ──────────
BG_DARK      = "#0d1117"
BG_PANEL     = "#161b22"
BG_CARD      = "#21262d"
ACCENT_CYAN  = "#58a6ff"
ACCENT_GREEN = "#3fb950"
ACCENT_WARN  = "#d29922"
ACCENT_RED   = "#f85149"
TEXT_MAIN    = "#e6edf3"
TEXT_DIM     = "#8b949e"
BORDER       = "#30363d"