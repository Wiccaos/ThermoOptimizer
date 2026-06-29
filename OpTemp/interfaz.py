# ============================================================
#  Interfaz gráfica de OpTemp
# ============================================================
import os
import tkinter as tk
from tkinter import scrolledtext
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import psutil

from config import (
    INTERVALO_ACTUALIZACION,
    TEMP_CRITICA, TEMP_WARN,
    UMBRAL_ALERTA_DERIVADA, UMBRAL_WARN_DERIVADA,
    BG_DARK, BG_PANEL, BG_CARD,
    ACCENT_CYAN, ACCENT_GREEN, ACCENT_WARN, ACCENT_RED,
    TEXT_MAIN, TEXT_DIM, BORDER,
)
from modelos import ModeloTermico
from simulador import SimuladorCarga


class AplicacionOpTemp:
    """
    - Construir y gestionar la ventana Tkinter.
    - Ejecutar el bucle de predicción térmica.
    - Delegar cálculos a ModeloTermico.
    - Delegar el escenario de demostración a SimuladorCarga.
    """

    def __init__(self):
        self._modelo    = ModeloTermico()
        self._simulador = SimuladorCarga()
        self._job_id    = None

        # Curva base (estática, se calcula una sola vez)
        self._cargas_x = np.linspace(0, 100, 500)
        self._temp_y   = np.vectorize(self._modelo.temperatura)(self._cargas_x)

        self._construir_ventana()

    # ══════════════════════════════════════════════════════════
    #  CONSTRUCCIÓN DE LA VENTANA
    # ══════════════════════════════════════════════════════════

    def _construir_ventana(self) -> None:
        self._root = tk.Tk()
        self._root.title("OpTemp  |  Sistema Predictivo de Eficiencia Térmica")
        self._root.geometry("1280x720")
        self._root.configure(bg=BG_DARK)
        self._root.minsize(1000, 600)
        self._root.protocol("WM_DELETE_WINDOW", self._cerrar)

        self._construir_header()
        self._construir_metricas()
        self._construir_cuerpo()

    def _construir_header(self) -> None:
        header = tk.Frame(self._root, bg=BG_PANEL, height=50)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        tk.Label(header, text="⚡ OpTemp",
                 font=("Consolas", 15, "bold"),
                 fg=ACCENT_CYAN, bg=BG_PANEL
        ).pack(side=tk.LEFT, padx=18, pady=10)

        tk.Label(header,
                 text="Sistema Predictivo de Eficiencia Térmica  ·  INACAP  ·  Cálculo Diferencial",
                 font=("Arial", 9), fg=TEXT_DIM, bg=BG_PANEL
        ).pack(side=tk.LEFT, padx=4)

        self._lbl_modo = tk.Label(header, text="● EN REPOSO",
                                  font=("Consolas", 9, "bold"),
                                  fg=ACCENT_GREEN, bg=BG_PANEL)
        self._lbl_modo.pack(side=tk.RIGHT, padx=18)

    def _construir_metricas(self) -> None:
        bar = tk.Frame(self._root, bg=BG_DARK, height=85)
        bar.pack(fill=tk.X, padx=12, pady=(8, 0))
        bar.pack_propagate(False)

        self._lbl_cpu    = self._tarjeta(bar, "CARGA CPU",             "%",        0)
        self._lbl_temp   = self._tarjeta(bar, "TEMPERATURA  T(x)",     "°C",       1)
        self._lbl_deriv  = self._tarjeta(bar, "TASA DE CAMBIO  T'(x)", "°C / %",   2)
        self._lbl_tiempo = self._tarjeta(bar, "TIEMPO AL THROTTLING",  "segundos", 3)
        self._lbl_freq   = self._tarjeta(bar, "FRECUENCIA ÓPTIMA",     "GHz",      4)

    def _construir_cuerpo(self) -> None:
        body = tk.Frame(self._root, bg=BG_DARK)
        body.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        self._construir_grafico(body)
        self._construir_panel_derecho(body)

    def _construir_grafico(self, parent: tk.Frame) -> None:
        frame = tk.Frame(parent, bg=BG_PANEL,
                         highlightbackground=BORDER, highlightthickness=1)
        frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        plt.style.use("dark_background")
        self._fig, self._ax = plt.subplots(figsize=(7, 5))
        self._fig.patch.set_facecolor(BG_PANEL)
        self._ax.set_facecolor(BG_CARD)

        self._canvas = FigureCanvasTkAgg(self._fig, master=frame)
        self._canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

    def _construir_panel_derecho(self, parent: tk.Frame) -> None:
        panel = tk.Frame(parent, bg=BG_DARK, width=360)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)

        tk.Label(panel, text="■ REGISTRO PREDICTIVO",
                 font=("Consolas", 9, "bold"),
                 fg=ACCENT_CYAN, bg=BG_DARK
        ).pack(anchor="w", pady=(0, 4))

        self._log_box = scrolledtext.ScrolledText(
            panel, wrap=tk.WORD, font=("Consolas", 8),
            bg="#010409", fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
            bd=0, relief=tk.FLAT,
            highlightbackground=BORDER, highlightthickness=1,
        )
        self._log_box.pack(fill=tk.BOTH, expand=True)
        self._log_box.tag_config("info",  foreground=ACCENT_GREEN)
        self._log_box.tag_config("warn",  foreground=ACCENT_WARN,
                                 font=("Consolas", 8, "bold"))
        self._log_box.tag_config("alert", foreground=ACCENT_RED,
                                 font=("Consolas", 8, "bold"))
        self._log_box.tag_config("sys",   foreground=ACCENT_CYAN)

        self._construir_botones(panel)

    def _construir_botones(self, parent: tk.Frame) -> None:
        f1 = tk.Frame(parent, bg=BG_DARK)
        f1.pack(fill=tk.X, pady=(8, 0))

        self._btn_sim  = self._boton(f1, "▶  SIMULAR ESCENARIO CRÍTICO",
                                     self._iniciar_simulacion, BG_DARK, ACCENT_WARN)
        self._btn_stop = self._boton(f1, "■  DETENER",
                                     self._detener_simulacion, BG_DARK, ACCENT_RED)
        self._btn_stop.config(state=tk.DISABLED)

        f2 = tk.Frame(parent, bg=BG_DARK)
        f2.pack(fill=tk.X, pady=(4, 0))
        self._boton(f2, "🗑  LIMPIAR REGISTRO", self._limpiar_log, TEXT_DIM, BG_CARD)

    # ══════════════════════════════════════════════════════════
    #  WIDGETS
    # ══════════════════════════════════════════════════════════

    def _tarjeta(self, parent: tk.Frame, titulo: str,
                 unidad: str, col: int) -> tk.Label:
        card = tk.Frame(parent, bg=BG_CARD,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                  padx=(0 if col == 0 else 6, 0))
        tk.Label(card, text=titulo, font=("Arial", 7, "bold"),
                 fg=TEXT_DIM, bg=BG_CARD).pack(anchor="w", padx=10, pady=(6, 0))
        lbl = tk.Label(card, text="---", font=("Consolas", 19, "bold"),
                       fg=TEXT_MAIN, bg=BG_CARD)
        lbl.pack(anchor="w", padx=10)
        tk.Label(card, text=unidad, font=("Arial", 7),
                 fg=TEXT_DIM, bg=BG_CARD).pack(anchor="w", padx=10, pady=(0, 6))
        return lbl

    def _boton(self, parent: tk.Frame, texto: str, comando,
               fg: str, bg: str) -> tk.Button:
        b = tk.Button(parent, text=texto, command=comando,
                      font=("Consolas", 8, "bold"), fg=fg, bg=bg,
                      activeforeground=BG_DARK, activebackground=fg,
                      relief=tk.FLAT, bd=0, cursor="hand2", padx=10, pady=6)
        b.pack(side=tk.LEFT, padx=(0, 6), fill=tk.X, expand=True)
        return b

    # ══════════════════════════════════════════════════════════
    #  ACCIONES DE CONTROL
    # ══════════════════════════════════════════════════════════

    def _iniciar_simulacion(self) -> None:
        self._simulador.iniciar()
        self._lbl_modo.config(text="◉ SIMULANDO ESCENARIO CRÍTICO", fg=ACCENT_WARN)
        self._log("Escenario predictivo iniciado: subida de carga 5% → 85%", "sys")
        self._log("OpTemp calculará el tiempo estimado al throttling en cada ciclo.", "sys")
        self._btn_sim.config(state=tk.DISABLED)
        self._btn_stop.config(state=tk.NORMAL)

    def _detener_simulacion(self) -> None:
        self._simulador.detener()
        self._lbl_modo.config(text="● EN REPOSO", fg=ACCENT_GREEN)
        self._log("Simulación detenida. Retomando lectura de CPU real.", "sys")
        self._btn_sim.config(state=tk.NORMAL)
        self._btn_stop.config(state=tk.DISABLED)

    def _limpiar_log(self) -> None:
        self._log_box.delete("1.0", tk.END)
        self._log("Registro limpiado.", "sys")

    def _cerrar(self) -> None:
        if self._job_id:
            self._root.after_cancel(self._job_id)
        plt.close("all")
        self._root.quit()
        self._root.destroy()
        os._exit(0)

    # ══════════════════════════════════════════════════════════
    #  LOG
    # ══════════════════════════════════════════════════════════

    def _log(self, msg: str, nivel: str = "info") -> None:
        hora   = datetime.now().strftime("%H:%M:%S")
        prefix = {"info": "[INFO ]", "warn": "[WARN ]",
                  "alert": "[ALERT]", "sys":  "[SYS  ]"}.get(nivel, "[INFO ]")
        self._log_box.insert(tk.END, f"{hora}  {prefix}  {msg}\n", nivel)
        self._log_box.see(tk.END)

    # ══════════════════════════════════════════════════════════
    #  CICLO DE PREDICCIÓN
    # ══════════════════════════════════════════════════════════

    def _obtener_carga(self) -> float:
        """Lee la carga del simulador o del CPU real según el modo activo."""
        if self._simulador.activo:
            carga = self._simulador.siguiente()
            if carga is None:
                self._detener_simulacion()
                return psutil.cpu_percent(interval=None)
            return carga
        return psutil.cpu_percent(interval=None)

    def _determinar_nivel(self, temp: float, derivada: float) -> str:
        if temp >= TEMP_CRITICA or derivada >= UMBRAL_ALERTA_DERIVADA:
            return "alert"
        if temp >= TEMP_WARN or derivada >= UMBRAL_WARN_DERIVADA:
            return "warn"
        return "info"

    def _actualizar_tarjetas(self, carga: float, temp: float,
                              derivada: float, freq: float,
                              t_critico: float | None, nivel: str) -> None:
        color_d = {
            "alert": ACCENT_RED, "warn": ACCENT_WARN, "info": ACCENT_GREEN
        }[nivel]

        self._lbl_cpu.config(text=f"{carga:.1f}", fg=ACCENT_CYAN)
        self._lbl_temp.config(
            text=f"{temp:.1f}",
            fg=ACCENT_RED if temp >= TEMP_CRITICA else
               ACCENT_WARN if temp >= TEMP_WARN else ACCENT_GREEN,
        )
        self._lbl_deriv.config(text=f"{derivada:.4f}", fg=color_d)
        self._lbl_freq.config(text=f"{freq:.2f}", fg=ACCENT_CYAN)

        if temp >= TEMP_CRITICA:
            self._lbl_tiempo.config(text="¡THROTTLING!", fg=ACCENT_RED)
        elif t_critico is not None:
            self._lbl_tiempo.config(text=f"~{t_critico:.0f}", fg=color_d)
        else:
            self._lbl_tiempo.config(text="ESTABLE", fg=ACCENT_GREEN)

    def _actualizar_grafico(self, carga: float, temp: float,
                             derivada: float, t_critico: float | None,
                             nivel: str) -> None:
        ax = self._ax
        ax.clear()
        ax.set_facecolor(BG_CARD)

        # Curva T(x)
        ax.plot(self._cargas_x, self._temp_y,
                color=ACCENT_CYAN, linewidth=2,
                label="T(x) = 0.004x² + 0.1x + 35")

        # Zonas de temperatura
        ax.axhspan(TEMP_CRITICA, 97, alpha=0.13, color=ACCENT_RED,
                   label=f"Zona crítica (≥{TEMP_CRITICA:.0f} °C)")
        ax.axhspan(TEMP_WARN, TEMP_CRITICA, alpha=0.08, color=ACCENT_WARN,
                   label=f"Advertencia ({TEMP_WARN:.0f}–{TEMP_CRITICA:.0f} °C)")

        # Recta tangente T'(x)
        color_recta = (ACCENT_RED if nivel == "alert" else
                       ACCENT_WARN if nivel == "warn" else "#888888")
        recta = derivada * (self._cargas_x - carga) + temp
        ax.plot(self._cargas_x, recta, "--", color=color_recta, linewidth=1.4,
                label=f"T'({carga:.0f}%) = {derivada:.4f} °C/%")

        # Proyección al punto de throttling
        if t_critico is not None and nivel in ("warn", "alert"):
            delta_carga_proj = (TEMP_CRITICA - temp) / derivada
            carga_proj = min(carga + delta_carga_proj, 100)
            ax.scatter(carga_proj, TEMP_CRITICA,
                       color=ACCENT_RED, s=90, marker="X", zorder=7,
                       label=f"Throttling proyectado ({carga_proj:.0f}%)")
            ax.annotate(f"  ⚠ ~{t_critico:.0f}s",
                        xy=(carga_proj, TEMP_CRITICA),
                        fontsize=8, color=ACCENT_RED,
                        xytext=(carga_proj + 2, TEMP_CRITICA + 1))

        # Punto actual
        ax.scatter(carga, temp,
                   color=ACCENT_RED if nivel == "alert" else ACCENT_CYAN,
                   s=70, zorder=6, edgecolors="white", linewidths=0.8)
        ax.annotate(f"  ({carga:.0f}%, {temp:.1f}°C)",
                    xy=(carga, temp), fontsize=8, color=TEXT_MAIN,
                    xytext=(carga + 2, temp + 1))

        ax.set_title("Modelo Predictivo Térmico — OpTemp",
                     fontsize=10, fontweight="bold", color=TEXT_MAIN, pad=10)
        ax.set_xlabel("Uso de CPU (%)", fontsize=8, color=TEXT_DIM)
        ax.set_ylabel("Temperatura Estimada T(x)  [°C]", fontsize=8, color=TEXT_DIM)
        ax.set_xlim(0, 100)
        ax.set_ylim(30, 97)
        ax.tick_params(colors=TEXT_DIM, labelsize=7)
        ax.spines[:].set_color(BORDER)
        ax.grid(True, linestyle=":", alpha=0.3, color=TEXT_DIM)
        ax.legend(loc="upper left", fontsize=7,
                  facecolor=BG_PANEL, edgecolor=BORDER, labelcolor=TEXT_MAIN)

        self._fig.tight_layout()
        self._canvas.draw()

    def _actualizar_log(self, carga: float, temp: float, derivada: float,
                        freq: float, t_critico: float | None, nivel: str) -> None:
        base = f"CPU {carga:.0f}% | T={temp:.1f}°C | T'={derivada:.4f}"
        if temp >= TEMP_CRITICA:
            self._log(f"{base} — ¡THROTTLING ACTIVO!", "alert")
        elif nivel == "alert":
            self._log(f"{base} — Throttling en ~{t_critico:.0f}s. Reducir carga.", "alert")
        elif nivel == "warn":
            self._log(f"{base} — Throttling estimado en ~{t_critico:.0f}s. Monitorear.", "warn")
        else:
            self._log(f"{base} | f_opt={freq:.2f} GHz — Sistema estable.", "info")

    def _ciclo(self) -> None:
        """Ciclo principal: obtiene datos, calcula y actualiza la UI."""
        carga     = self._obtener_carga()
        temp      = self._modelo.temperatura(carga)
        derivada  = self._modelo.tasa_de_cambio(carga)
        freq      = self._modelo.frecuencia_optima(temp)
        t_critico = self._modelo.tiempo_al_throttling(temp, derivada)
        nivel     = self._determinar_nivel(temp, derivada)

        self._actualizar_tarjetas(carga, temp, derivada, freq, t_critico, nivel)
        self._actualizar_grafico(carga, temp, derivada, t_critico, nivel)
        self._actualizar_log(carga, temp, derivada, freq, t_critico, nivel)

        self._job_id = self._root.after(INTERVALO_ACTUALIZACION, self._ciclo)

    # ══════════════════════════════════════════════════════════
    #  ARRANQUE
    # ══════════════════════════════════════════════════════════

    def ejecutar(self) -> None:
        """Inicia la aplicación."""
        psutil.cpu_percent(interval=0.1)   # descarte de lectura inicial nula
        self._log("OpTemp iniciado — Sistema Predictivo de Eficiencia Térmica.", "sys")
        self._log("Modelo: T(x)=0.004x²+0.1x+35  |  T'(x)=0.008x+0.1", "sys")
        self._log(f"Umbral throttling: {TEMP_CRITICA}°C  |  Advertencia: {TEMP_WARN}°C", "sys")
        self._log("Presiona '▶ SIMULAR' para activar el escenario predictivo.", "info")
        self._ciclo()
        self._root.mainloop()