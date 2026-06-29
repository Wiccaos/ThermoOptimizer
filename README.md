# OpTemp — Sistema Predictivo de Eficiencia Térmica

> Proyecto final ABPro — Cálculo Diferencial · Ingeniería en Informática · INACAP Temuco  
> **Docente:** Marisel Hueche Caifual · **Fecha de presentación:** 02 de Julio de 2026

**OpTemp** es un prototipo de software que aplica cálculo diferencial para **predecir** el sobrecalentamiento de microprocesadores antes de que ocurra, en lugar de reaccionar cuando ya es demasiado tarde.

---

## Contexto del problema

Los centros de datos modernos destinan más del **40% de su consumo eléctrico** al enfriamiento activo de CPU y GPU. Cuando un procesador supera su límite térmico seguro (~70 °C), entra en *thermal throttling*: se ralentiza automáticamente para protegerse, cayendo el rendimiento de forma drástica.

Los reguladores tradicionales son **reactivos**: actúan cuando el chip ya se sobrecalentó. OpTemp propone un enfoque **predictivo**: usando la primera derivada de la función térmica, estima en cuántos segundos se alcanzará el punto crítico y actúa con anticipación.

---

## 📐 Modelo matemático

El proyecto se basa en tres conceptos de Cálculo Diferencial:

### 1. Función de temperatura
```
T(x) = 0.004x² + 0.1x + 35
```
Modela la temperatura del microprocesador (°C) en función del porcentaje de uso `x` (0–100%). El comportamiento cuadrático refleja el calentamiento resistivo del silicio.

### 2. Primera derivada — Tasa de cambio instantánea
```
T'(x) = 0.008x + 0.1
```
Describe qué tan rápido está subiendo la temperatura en un instante dado. Es el indicador central del sistema de alertas.

### 3. Predicción temporal (Ley de Newton modificada)
```
Δt = ΔT / T'(x)
```
Donde `ΔT = T_crítica − T_actual`. Estima los segundos restantes antes del throttling asumiendo que la tasa de cambio se mantiene constante.

### 4. Frecuencia óptima de operación
```
f_opt = 4.0 − (T − 35) × (1.6 / 40)   [GHz]
```
Punto de operación que maximiza la eficiencia energética (GigaFlops/Watt) bajo el criterio de la primera derivada (`dU/df = 0`).
