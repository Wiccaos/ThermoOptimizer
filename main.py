import os
import tkinter as tk
from tkinter import scrolledtext, ttk
import psutil
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

# ============================================================
#  CONFIGURACIÓN GLOBAL
# ============================================================
INTERVALO_ACTUALIZACION = 1500          # ms entre lecturas
UMBRAL_ALERTA_DERIVADA  = 0.65         # T'(x) crítica
UMBRAL_WARN_DERIVADA    = 0.45         # T'(x) advertencia

# Paleta de colores (tema oscuro tipo "data-center")
BG_DARK     = "#0d1117"
BG_PANEL    = "#161b22"
BG_CARD     = "#21262d"
ACCENT_CYAN = "#58a6ff"
ACCENT_GREEN= "#3fb950"
ACCENT_WARN = "#d29922"
ACCENT_RED  = "#f85149"
TEXT_MAIN   = "#e6edf3"
TEXT_DIM    = "#8b949e"
BORDER      = "#30363d"

# ============================================================
#  MODELOS MATEMÁTICOS
# ============================================================
def calcular_temperatura(carga: float) -> float:
    """T(x) = 0.004x² + 0.1x + 35"""
    return 0.004 * (carga ** 2) + 0.1 * carga + 35

def calcular_razon_cambio(carga: float) -> float:
    """T'(x) = 0.008x + 0.1  (primera derivada de T)"""
    return 0.008 * carga + 0.1

def calcular_frecuencia_optima(temp: float) -> float:
    """
    Frecuencia sugerida en GHz basada en temperatura.
    Escala linealmente de 4.0 GHz (35 °C) a 2.4 GHz (75 °C).
    """
    freq = 4.0 - (temp - 35) * (1.6 / 40)
    return max(2.4, min(4.0, freq))

# ============================================================
#  ESCENARIO DE SIMULACIÓN
# ============================================================
class SimuladorCarga:
    """
    Genera una curva de carga simulada sin estresar el hardware.
    Fase 1: sube gradualmente de 5% → 85% (carga crítica)
    Fase 2: mantiene carga alta con pequeñas oscilaciones
    Fase 3: baja gradualmente (enfriamiento)
    """
    def __init__(self):
        self.activo   = False
        self.paso     = 0
        self._secuencia = self._generar_secuencia()

    def _generar_secuencia(self):
        subida    = np.linspace(5,  85, 20)
        alta      = 85 + np.random.uniform(-4, 4, 15)
        bajada    = np.linspace(85, 20, 15)
        reposo    = 20 + np.random.uniform(-3, 3, 10)
        return np.concatenate([subida, alta, bajada, reposo])

    def siguiente(self) -> float:
        if not self.activo:
            return None
        val = self._secuencia[self.paso % len(self._secuencia)]
        self.paso += 1
        if self.paso >= len(self._secuencia):
            self.activo = False   # simulación terminó
            self.paso   = 0
        return float(val)

    def iniciar(self):
        self.paso    = 0
        self.activo  = True
        self._secuencia = self._generar_secuencia()

    def detener(self):
        self.activo = False
        self.paso   = 0

# ============================================================
#  INTERFAZ PRINCIPAL
# ============================================================
def inicializar_interfaz():
    simulador = SimuladorCarga()

    # ── Ventana raíz ──────────────────────────────────────────
    root = tk.Tk()
    root.title("ThermoOptimizer Pro  |  Monitor Térmico en Tiempo Real")
    root.geometry("1280x720")
    root.configure(bg=BG_DARK)
    root.minsize(1000, 600)

    # Cierre limpio: cancela el after pendiente, cierra matplotlib
    _job_id = [None]
    def on_cerrar():
        if _job_id[0]:
            root.after_cancel(_job_id[0])
        plt.close("all")
        root.quit()
        root.destroy()
        os._exit(0)
    root.protocol("WM_DELETE_WINDOW", on_cerrar)

    # ── Barra de título superior ──────────────────────────────
    header = tk.Frame(root, bg=BG_PANEL, height=50, bd=0)
    header.pack(fill=tk.X, side=tk.TOP)
    header.pack_propagate(False)

    tk.Label(
        header, text="⚡ ThermoOptimizer Pro",
        font=("Consolas", 15, "bold"),
        fg=ACCENT_CYAN, bg=BG_PANEL
    ).pack(side=tk.LEFT, padx=18, pady=10)

    tk.Label(
        header, text="INACAP  ·  Cálculo Diferencial  ·  Ingeniería en Informática",
        font=("Arial", 9), fg=TEXT_DIM, bg=BG_PANEL
    ).pack(side=tk.LEFT, padx=4, pady=10)

    # Indicador de modo (tiempo real / simulación)
    lbl_modo = tk.Label(
        header, text="● TIEMPO REAL",
        font=("Consolas", 9, "bold"),
        fg=ACCENT_GREEN, bg=BG_PANEL
    )
    lbl_modo.pack(side=tk.RIGHT, padx=18)

    # ── Panel de tarjetas métricas ────────────────────────────
    metrics_bar = tk.Frame(root, bg=BG_DARK, height=80)
    metrics_bar.pack(fill=tk.X, padx=12, pady=(8, 0))
    metrics_bar.pack_propagate(False)

    def crear_tarjeta(parent, titulo, valor_inicial, unidad, col):
        card = tk.Frame(parent, bg=BG_CARD, bd=0, relief=tk.FLAT,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                  padx=(0 if col == 0 else 6, 0))
        tk.Label(card, text=titulo, font=("Arial", 8),
                 fg=TEXT_DIM, bg=BG_CARD).pack(anchor="w", padx=10, pady=(6,0))
        lbl_val = tk.Label(card, text=valor_inicial,
                           font=("Consolas", 20, "bold"),
                           fg=TEXT_MAIN, bg=BG_CARD)
        lbl_val.pack(anchor="w", padx=10)
        tk.Label(card, text=unidad, font=("Arial", 7),
                 fg=TEXT_DIM, bg=BG_CARD).pack(anchor="w", padx=10, pady=(0,6))
        return lbl_val

    lbl_cpu  = crear_tarjeta(metrics_bar, "USO DE CPU",      "---",   "%",       0)
    lbl_temp = crear_tarjeta(metrics_bar, "TEMPERATURA T(x)","---",   "°C",      1)
    lbl_deriv= crear_tarjeta(metrics_bar, "RAZÓN DE CAMBIO T'(x)","---","°C / %",2)
    lbl_freq = crear_tarjeta(metrics_bar, "FRECUENCIA ÓPTIMA","---",  "GHz",     3)

    # ── Cuerpo principal (gráfico + logs) ─────────────────────
    body = tk.Frame(root, bg=BG_DARK)
    body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

    # Panel gráfico
    grafico_frame = tk.Frame(body, bg=BG_PANEL,
                             highlightbackground=BORDER, highlightthickness=1)
    grafico_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

    # Matplotlib con fondo oscuro
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(7, 5))
    fig.patch.set_facecolor(BG_PANEL)
    ax.set_facecolor(BG_CARD)
    canvas = FigureCanvasTkAgg(fig, master=grafico_frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    cargas_x = np.linspace(0, 100, 500)
    temp_y   = calcular_temperatura(cargas_x)

    # Panel derecho (logs + botones)
    panel_der = tk.Frame(body, bg=BG_DARK, width=360)
    panel_der.pack(side=tk.RIGHT, fill=tk.Y)
    panel_der.pack_propagate(False)

    # ── Log / consola ─────────────────────────────────────────
    tk.Label(panel_der,
             text="■ PANEL DE ALERTAS Y LOGS",
             font=("Consolas", 9, "bold"),
             fg=ACCENT_CYAN, bg=BG_DARK
    ).pack(anchor="w", pady=(0,4))

    log_box = scrolledtext.ScrolledText(
        panel_der, wrap=tk.WORD,
        font=("Consolas", 8),
        bg="#010409", fg=TEXT_MAIN,
        insertbackground=TEXT_MAIN,
        bd=0, relief=tk.FLAT,
        highlightbackground=BORDER, highlightthickness=1
    )
    log_box.pack(fill=tk.BOTH, expand=True)

    # Etiquetas de color para el log
    log_box.tag_config("info",  foreground=ACCENT_GREEN)
    log_box.tag_config("warn",  foreground=ACCENT_WARN, font=("Consolas", 8, "bold"))
    log_box.tag_config("alert", foreground=ACCENT_RED,  font=("Consolas", 8, "bold"))
    log_box.tag_config("sys",   foreground=ACCENT_CYAN)
    log_box.tag_config("dim",   foreground=TEXT_DIM)

    def registrar_log(mensaje: str, nivel: str = "info"):
        hora = datetime.now().strftime("%H:%M:%S")
        etiquetas = {
            "info":  "[INFO ]",
            "warn":  "[WARN ]",
            "alert": "[ALERT]",
            "sys":   "[SYS  ]",
        }
        etiqueta = etiquetas.get(nivel, "[INFO ]")
        linea = f"{hora}  {etiqueta}  {mensaje}\n"
        log_box.insert(tk.END, linea, nivel)
        log_box.see(tk.END)

    # ── Botones de control ────────────────────────────────────
    ctrl_frame = tk.Frame(panel_der, bg=BG_DARK)
    ctrl_frame.pack(fill=tk.X, pady=(8, 0))

    def estilo_boton(frame, texto, comando, color_fg, color_bg):
        b = tk.Button(
            frame, text=texto, command=comando,
            font=("Consolas", 8, "bold"),
            fg=color_fg, bg=color_bg,
            activeforeground=BG_DARK, activebackground=color_fg,
            relief=tk.FLAT, bd=0, cursor="hand2",
            padx=10, pady=6
        )
        b.pack(side=tk.LEFT, padx=(0, 6), fill=tk.X, expand=True)
        return b

    def iniciar_simulacion():
        simulador.iniciar()
        lbl_modo.config(text="◉ SIMULANDO CARGA CRÍTICA", fg=ACCENT_WARN)
        registrar_log("Modo simulación activado. Escenario de carga crítica iniciado.", "sys")
        btn_sim.config(state=tk.DISABLED)
        btn_stop.config(state=tk.NORMAL)

    def detener_simulacion():
        simulador.detener()
        lbl_modo.config(text="● TIEMPO REAL", fg=ACCENT_GREEN)
        registrar_log("Simulación detenida. Volviendo a lectura en tiempo real.", "sys")
        btn_sim.config(state=tk.NORMAL)
        btn_stop.config(state=tk.DISABLED)

    def limpiar_logs():
        log_box.delete("1.0", tk.END)
        registrar_log("Log limpiado.", "sys")

    btn_sim  = estilo_boton(ctrl_frame, "▶  SIMULAR CARGA CRÍTICA", iniciar_simulacion, BG_DARK, ACCENT_WARN)
    btn_stop = estilo_boton(ctrl_frame, "■  DETENER",               detener_simulacion, BG_DARK, ACCENT_RED)
    btn_stop.config(state=tk.DISABLED)

    ctrl_frame2 = tk.Frame(panel_der, bg=BG_DARK)
    ctrl_frame2.pack(fill=tk.X, pady=(4, 0))
    estilo_boton(ctrl_frame2, "🗑  LIMPIAR LOG", limpiar_logs, TEXT_DIM, BG_CARD)

    # ── Bucle de actualización ────────────────────────────────
    def actualizar_datos():
        # Obtener carga: simulada o real
        if simulador.activo:
            uso_cpu = simulador.siguiente()
            if uso_cpu is None:          # simulación terminó
                detener_simulacion()
                uso_cpu = psutil.cpu_percent(interval=None)
        else:
            uso_cpu = psutil.cpu_percent(interval=None)

        temp_actual    = calcular_temperatura(uso_cpu)
        derivada_actual= calcular_razon_cambio(uso_cpu)
        freq_optima    = calcular_frecuencia_optima(temp_actual)

        # Determinar nivel de alerta
        if derivada_actual >= UMBRAL_ALERTA_DERIVADA:
            nivel       = "alert"
            color_deriv = ACCENT_RED
        elif derivada_actual >= UMBRAL_WARN_DERIVADA:
            nivel       = "warn"
            color_deriv = ACCENT_WARN
        else:
            nivel       = "info"
            color_deriv = ACCENT_GREEN

        # ── Actualizar tarjetas métricas ──────────────────────
        lbl_cpu.config(  text=f"{uso_cpu:.1f}",        fg=ACCENT_CYAN)
        lbl_temp.config( text=f"{temp_actual:.1f}",
                         fg=ACCENT_RED if temp_actual > 70 else
                            ACCENT_WARN if temp_actual > 55 else ACCENT_GREEN)
        lbl_deriv.config(text=f"{derivada_actual:.4f}", fg=color_deriv)
        lbl_freq.config( text=f"{freq_optima:.2f}",    fg=ACCENT_CYAN)

        # ── Actualizar gráfico ────────────────────────────────
        ax.clear()
        ax.set_facecolor(BG_CARD)

        # Curva térmica
        ax.plot(cargas_x, temp_y,
                color=ACCENT_CYAN, linewidth=2,
                label="T(x) = 0.004x² + 0.1x + 35")

        # Zona de peligro
        ax.axhspan(70, 95, alpha=0.12, color=ACCENT_RED, label="Zona crítica (>70 °C)")
        ax.axhspan(55, 70, alpha=0.08, color=ACCENT_WARN, label="Zona de advertencia")

        # Recta tangente
        recta = derivada_actual * (cargas_x - uso_cpu) + temp_actual
        ax.plot(cargas_x, recta, '--',
                color=ACCENT_RED if nivel == "alert" else ACCENT_WARN if nivel == "warn" else "#aaa",
                linewidth=1.4,
                label=f"T'({uso_cpu:.0f}%) = {derivada_actual:.4f} °C/%")

        # Punto actual
        ax.scatter(uso_cpu, temp_actual,
                   color=ACCENT_RED if nivel == "alert" else ACCENT_CYAN,
                   s=70, zorder=6, edgecolors="white", linewidths=0.8)

        # Anotación del punto
        ax.annotate(
            f"  ({uso_cpu:.0f}%, {temp_actual:.1f}°C)",
            xy=(uso_cpu, temp_actual),
            fontsize=8, color=TEXT_MAIN,
            xytext=(uso_cpu + 3, temp_actual + 1)
        )

        ax.set_title("Cálculo Diferencial en Vivo — Curva Térmica CPU",
                     fontsize=10, fontweight="bold", color=TEXT_MAIN, pad=10)
        ax.set_xlabel("Uso de CPU (%)", fontsize=8, color=TEXT_DIM)
        ax.set_ylabel("Temperatura Estimada (°C)", fontsize=8, color=TEXT_DIM)
        ax.set_xlim(0, 100)
        ax.set_ylim(30, 95)
        ax.tick_params(colors=TEXT_DIM, labelsize=7)
        ax.spines[:].set_color(BORDER)
        ax.grid(True, linestyle=':', alpha=0.3, color=TEXT_DIM)
        ax.legend(loc="upper left", fontsize=7,
                  facecolor=BG_PANEL, edgecolor=BORDER, labelcolor=TEXT_MAIN)

        fig.tight_layout()
        canvas.draw()

        # ── Log de alertas ────────────────────────────────────
        if nivel == "alert":
            registrar_log(
                f"CPU {uso_cpu:.0f}% | T={temp_actual:.1f}°C | T'={derivada_actual:.4f} — TASA TÉRMICA CRÍTICA",
                "alert"
            )
        elif nivel == "warn":
            registrar_log(
                f"CPU {uso_cpu:.0f}% | T={temp_actual:.1f}°C | T'={derivada_actual:.4f} — Tasa en ascenso",
                "warn"
            )
        else:
            registrar_log(
                f"CPU {uso_cpu:.0f}% | T={temp_actual:.1f}°C | T'={derivada_actual:.4f} | f_opt={freq_optima:.2f} GHz",
                "info"
            )

        # Reprogramar si la ventana sigue viva
        _job_id[0] = root.after(INTERVALO_ACTUALIZACION, actualizar_datos)

    # ── Arranque ──────────────────────────────────────────────
    psutil.cpu_percent(interval=0.1)          # descarte lectura inicial nula
    registrar_log("ThermoOptimizer Pro iniciado.", "sys")
    registrar_log("Funciones: T(x)=0.004x²+0.1x+35  |  T'(x)=0.008x+0.1", "sys")
    registrar_log(f"Umbral WARN={UMBRAL_WARN_DERIVADA}  |  Umbral ALERT={UMBRAL_ALERTA_DERIVADA}", "sys")
    registrar_log("Lectura de CPU en tiempo real activa...", "info")

    actualizar_datos()
    root.mainloop()


if __name__ == "__main__":
    inicializar_interfaz()