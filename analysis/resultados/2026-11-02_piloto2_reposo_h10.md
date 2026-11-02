# Piloto 2 · Reposo con Hex real y Polar H10 · 2026-11-02

**Equipo:** Humon Hex BD2 (HW 17.3 · FW 1.10.0) · **Polar H10** (banda torácica ECG). Antes se usaba el brazalete óptico Chileaf CL837.
**Sesión:** 7 min 07 s en reposo · participante **P001** · sin marcadores.

## 1. Calidad de los datos

| Medida | Piloto 1 (CL837) | Piloto 2 (H10) |
|---|---|---|
| Frecuencia CALC / RAW | 3,92 Hz | 3,92 Hz |
| Irregularidad (jitter) | 53 ms | **9 ms** |
| Huecos > 1 s | 1 | 0 |
| Paquetes incoherentes | 0 | 0 |
| RR: cobertura | 55 % | **100 %** |
| RR: artefactos | 39 % | **0 %** |
| DFA‑α1 calculable | no | **sí** (23 ventanas) |

**Conclusión:** la H10 entrega RR aptos para DFA‑α1. El brazalete óptico CL837 **no es apto para variabilidad de la FC**: pierde casi la mitad de los latidos y sus RR tienen muchos artefactos. Esto también vale para cualquier análisis que use RR de ese brazalete.

## 2. SmO₂ y zona del firmware

- SmO₂ en reposo **estable, 52–59 %**, con 100 % del tiempo en zonas 2–3. Ya no aparecen las zonas 4–5 falsas del piloto 1, lo que apoya la hipótesis de compresión del muslo en ese registro.
- El basal (~57 %) difiere mucho del piloto 1 (~70–75 %) en la misma persona. **La SmO₂ absoluta depende de la colocación**: hay que trabajar con valores relativos al basal de cada sesión, como hace el firmware con sus zonas.

## 3. DFA‑α1 en reposo

α1 entre **0,93 y 1,41**: lo esperado en reposo (α1 ≥ 1, dinámica correlacionada). Los umbrales por DFA requieren ejercicio progresivo (FC con rango amplio); en reposo no se pueden estimar, y la app lo informa así correctamente.

## 4. ¿Pulso cardíaco en la señal cruda del Hex? → **No detectable**

Dos pruebas independientes:

1. **Espectro (Lomb–Scargle):** pico a la FC de la H10 (±5 lpm) en solo **1 de 13** ventanas de 60 s. Los picos se dispersan entre 44 y 57 lpm (FC real 60–65), con correlación Hex–banda r = 0,29.
2. **Promedio sincronizado con cada latido de la H10:** con los tiempos exactos de los latidos se buscó una componente pulsátil en fase en cada uno de los 8 canales RAW. **Ningún canal supera el nivel de azar** (prueba de permutación, p95).

La señal tiene resolución de sobra (variación rápida de 0,2 a 1,7 % sobre cientos de cuentas), pero **no contiene un pulso recuperable**. Es coherente con el diseño descrito en la patente: integración de 100–300 ms y muestreo lento, pensados justamente para promediar el pulso y el movimiento.

El pico cercano a la FC del piloto 1 no se reprodujo: probablemente fue un artefacto.

**Decisión: se descarta estimar la FC desde el Hex.** La FC se mantiene desde una banda torácica ECG. El criterio queda abierto: se reevaluaría solo si aparece un modo de muestreo más rápido en el firmware.

## Siguiente paso

Prueba incremental con lactato capilar por fase (y CPET si es posible), H10 y modo investigación. Con eso se comparan contra el lactato medido el bilineal de SmO₂, el inicio de zona roja, el quiebre SmO₂–FC y DFA‑α1.
