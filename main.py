import tkinter as tk
from tkinter import scrolledtext
import psutil
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime

# --- CONFIGURACIÓN DE PARÁMETROS ---
INTERVALO_ACTUALIZACION = 2000 # Intervalo de actualización en 2 segundos
UMBRAL_ALERTA_DERIVADA = 0.65  # Punto crítico de la razón de cambio

# --- FUNCIONES MATEMÁTICAS ---
def calcular_temperatura(carga):
    """ T(x) = 0.004x^2 + 0.1x + 35"""
    return 0.004 * (carga**2) + 0.1 * carga + 35

def calcular_razon_cambio(carga):
    """ T'(x) = 0.008x + 0.1 """
    return 0.008 * carga + 0.1

# --- LÓGICA DE LA INTERFAZ GRÁFICA ---
def inicializar_interfaz():
    root = tk.Tk()
    root.title("ThermoOptimizer - Monitor en Tiempo Real")
    root.geometry("1100x600")
    root.configure(bg="#f0f0f0")

    # Contenedor principal
    main_frame = tk.Frame(root, bg="#f0f0f0")
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # Panel izquierdo (Gráfico)
    grafico_frame = tk.Frame(main_frame, bg="white", bd=2, relief=tk.SUNKEN)
    grafico_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))

    # Panel derecho (Notificaciones)
    panel_derecho = tk.Frame(main_frame, bg="#f0f0f0", width=400)
    panel_derecho.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
    panel_derecho.pack_propagate(False)

    # Título del panel de notificaciones
    lbl_titulo_log = tk.Label(panel_derecho, text="Panel de Alertas y Logs", font=("Arial", 12, "bold"), bg="#f0f0f0")
    lbl_titulo_log.pack(pady=(0, 10))

    # Caja de texto con scroll para los logs
    log_box = scrolledtext.ScrolledText(panel_derecho, wrap=tk.WORD, font=("Consolas", 9), bg="#1e1e1e", fg="#d4d4d4")
    log_box.pack(fill=tk.BOTH, expand=True)

    # Preparación de la figura de Matplotlib
    fig, ax = plt.subplots(figsize=(6, 5))
    canvas = FigureCanvasTkAgg(fig, master=grafico_frame)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Variables estáticas para el gráfico
    cargas_x = np.linspace(0, 100, 500)
    temp_y = calcular_temperatura(cargas_x)

    def registrar_log(mensaje, es_alerta=False):
        hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        etiqueta = "[ALERTA]" if es_alerta else "[INFO]"
        color = "red" if es_alerta else "green"
        
        texto_final = f"{hora_actual} {etiqueta} {mensaje}\n"
        log_box.insert(tk.END, texto_final)
        
        # Colorear alertas
        if es_alerta:
            start_index = log_box.index("end-2c linestart")
            end_index = log_box.index("end-1c")
            log_box.tag_add("alerta", start_index, end_index)
            log_box.tag_config("alerta", foreground="#ff5555", font=("Consolas", 9, "bold"))
            
        log_box.see(tk.END) # Autoscroll hacia abajo

    def actualizar_datos():
        # Leer uso del CPU en tiempo real
        uso_cpu = psutil.cpu_percent(interval=None)
        
        # Aplicar modelos matemáticos
        temp_actual = calcular_temperatura(uso_cpu)
        derivada_actual = calcular_razon_cambio(uso_cpu)

        # Actualizar Gráfico
        ax.clear()
        ax.plot(cargas_x, temp_y, color='darkblue', linewidth=2, label="Curva Térmica T(x)")
        
        # Dibujar recta tangente
        recta_tangente = derivada_actual * (cargas_x - uso_cpu) + temp_actual
        ax.plot(cargas_x, recta_tangente, '--', color='red', label=f"T'({uso_cpu}%) = {derivada_actual:.3f}")
        ax.scatter(uso_cpu, temp_actual, color='black', s=50, zorder=5)
        
        ax.set_title("Cálculo Diferencial en Vivo: CPU Térmica", fontweight="bold")
        ax.set_xlabel("Uso de CPU (%)")
        ax.set_ylabel("Temperatura Estimada (°C)")
        ax.set_xlim(0, 100)
        ax.set_ylim(30, 95)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(loc="upper left")
        
        canvas.draw()

        # Lógica del Sistema de Alertas
        if derivada_actual >= UMBRAL_ALERTA_DERIVADA:
            msg = f"CPU al {uso_cpu}%. Tasa térmica crítica (T'={derivada_actual:.3f})."
            registrar_log(msg, es_alerta=True)
        else:
            msg = f"Lectura normal. CPU: {uso_cpu}%, Temp: {temp_actual:.1f}°C"
            registrar_log(msg, es_alerta=False)

        # Programar la siguiente lectura (Bucle)
        root.after(INTERVALO_ACTUALIZACION, actualizar_datos)

    # Iniciar la primera lectura para evitar que el primer valor de psutil sea 0.0
    psutil.cpu_percent(interval=0.1)
    registrar_log("Iniciando monitoreo de hardware...", es_alerta=False)
    
    # Iniciar el bucle de actualización
    actualizar_datos()
    
    # Arrancar la ventana de Tkinter
    root.mainloop()

if __name__ == "__main__":
    inicializar_interfaz()