# Piloto 1 · Reposo con Hex real · 2026-11-02

**Equipo:** Humon Hex BD2 · modelo `hex` · HW 17.3 · FW 1.10.0 · banda de FC por Bluetooth.
**Sesión:** 8 min 10 s, sentado, tipo Resistencia, sin marcadores. Participante sin código (anon-6a5da7).
**Paquete:** no se publica (datos personales). Se analizó con `01_calidad.py` y `04_fc_desde_raw.py`.

## 1. Calidad del enlace Bluetooth (CALC y RAW)

| Medida | Valor |
|---|---|
| Frecuencia real CALC / RAW | **3,92 Hz** / 3,92 Hz (por hora de llegada) |
| Irregularidad (jitter) | ~53 ms |
| Huecos > 1 s | 1 |
| Paquetes incoherentes (HbO₂/tHb ≠ SmO₂) | 0 |
| Límite de Nyquist para FC | **~118 lpm** |

Confirma la frecuencia de ~4 Hz que reporta la validación publicada (Farzam 2018).

## 2. Calibración del firmware

Bloques A y B: oscuridad ≈ 2480–3020 cuentas por canal y potencia de 3289 a 38 872 cuentas. Es coherente con la calibración de oscuridad y de potencia del LED que describe la patente US10799162B2.

## 3. Zona del firmware en reposo

SmO₂ de 75,8 → 56,4 % (desaturación de 13 pts) **sentado y quieto**, con 37 % del tiempo en zonas 4–5.
Hipótesis: **compresión del muslo** (silla o banda muy ajustada), que reduce el flujo, o el Hex asentándose tras la colocación. Siguiente piloto: Hex en la cara anterior del muslo, sin apoyo en la silla, banda firme pero sin comprimir.

## 4. Intervalos RR de la banda

277 RR en 490 s · **cobertura 55 %** · **39 % de artefactos**. **No aptos para DFA‑α1**: la banda no envía todos los latidos, o sus RR son estimados (frecuente en brazaletes ópticos). Se requiere una banda torácica ECG (p. ej., Polar H10) con <5 % de artefactos.

## 5. ¿Pulso cardíaco en la señal cruda?

- Tramo completo (20–480 s): pico en **64 lpm** en raw1a y raw1b (banda 65 lpm). Los otros 6 canales no coinciden.
- Ventanas de 60 s: **10/14** dentro de ±5 lpm, con relaciones señal/ruido de hasta ~30 en las ventanas buenas.
- Pero el pico del Hex se queda **fijo en 61–63 lpm** mientras la banda varía entre 62 y 68 lpm (correlación r = −0,52), y 4 ventanas caen en ~41 lpm, el borde inferior de la búsqueda.

**Conclusión: no concluyente.** Hay una componente periódica cerca de la FC, pero en reposo la FC casi no varió, así que no se puede distinguir un pulso real de un artefacto. Por ejemplo, el parpadeo de la luz artificial (100 Hz) plegado por el muestreo de ~3,92 Hz cae cerca de 115 lpm, y en algunas ventanas aparece un pico en esa zona.

## Siguiente piloto (cómo confirmar o descartar)

1. Banda torácica ECG con RR completos.
2. Hex en la cara anterior del muslo, sin compresión, **cubierto con tela oscura** para descartar luz ambiente.
3. **3 min de reposo + 4 min de pedaleo suave** que suba la FC a 90–110 lpm (bajo Nyquist) + 2 min de reposo.
4. Código de participante en la ficha.
5. Criterio: el pico del Hex debe seguir a la banda (r > 0,8 y error < 5 lpm). Si se queda fijo, es un artefacto.
