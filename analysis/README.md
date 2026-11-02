# Análisis · ReadHumHex en modo investigación

Scripts para analizar los **paquetes de investigación** (`.json`, esquema `readhumhex-research/1`) que descarga la app al guardar una sesión con el **modo investigación** activado (pestaña *Dispositivos*).

> Objetivo: validar y mejorar, con datos abiertos y verificables, los algoritmos del sensor NIRS Humon Hex, descontinuado comercialmente: zonas, umbral, lactato y FC.

## Instalación

```bash
cd analysis
python3 -m pip install -r requirements.txt
```

## Scripts

| Script | Pregunta que responde |
|---|---|
| `01_calidad.py` | ¿Los datos sirven? Frecuencia real y *jitter* de CALC y RAW, huecos, coherencia HbO₂/tHb ≈ SmO₂, artefactos de RR, marcadores registrados. |
| `02_modelo_zonas.py` | ¿Se puede reproducir con reglas abiertas la **zona del firmware**? Árbol de decisión interpretable sobre nivel relativo y pendientes (10/30/60 s) de SmO₂, HbO₂, HHb y tHb, validado por sesión. |
| `03_umbrales_vs_referencia.py` | ¿Qué método de umbral concuerda mejor con el **lactato** (2 y 4 mmol/L)? Compara bilineal SmO₂–tiempo, **SmO₂–FC** (independiente de la actividad), HHb, inicio de zona roja y DFA‑α1 con Bland–Altman. |
| `04_fc_desde_raw.py` | ¿Contiene la **señal cruda** del Hex el pulso cardíaco? Espectro Lomb–Scargle en reposo comparado con la banda de FC. |

Todos aceptan varios paquetes: `python 03_umbrales_vs_referencia.py datos/*.json --csv resultados.csv`.

`sample/demo_P001_umbral.json` es un paquete **simulado** (modo demo, rotulado así dentro del archivo) para probar los scripts. **No es evidencia.** Su RAW incluye un pulso artificial, por eso `04` lo "detecta".

## Protocolo piloto sugerido

1. **Ficha:** crea al deportista con un **código de participante** (p. ej., P001). El paquete usa ese código, nunca el nombre. Registra el pliegue cutáneo en el sitio del sensor.
2. **Colocación:** Hex en el vasto lateral o el recto femoral, siempre en el mismo sitio, con banda torácica que envíe intervalos **RR**.
3. **Reposo:** 3 min sentado y quieto al inicio. Sirve para `04` (FC desde RAW) y para la línea basal.
4. **Prueba incremental** (pestaña *Umbral*): bicicleta 30 W + 30 W o cinta 5 + 1 km/h, fases de 3 min.
   - **Lactato capilar** en los últimos 30 s de cada fase. Regístralo en *Registrar muestra*: queda marcado en el tiempo exacto.
   - **CPET simultáneo** (p. ej., VO2Smart PRO). Registra VO₂, VE y RER por fase, o exporta el archivo del CPET y únelo por hora.
   - Agotamiento voluntario y **3 min de recuperación**.
5. **Test–retest:** repite la prueba a las 48–72 h, en las mismas condiciones, para medir la fiabilidad.

Con 10 o más deportistas y test–retest, `03` entrega sesgo y límites de acuerdo por método. Eso permite decidir qué algoritmo pasa de "experimental" a "validado" en la app.

## Ética y datos

- Estudios con personas: **aprobación de un comité de ética** y **consentimiento informado** antes de recolectar o compartir datos.
- Los paquetes no contienen nombres. Sí contienen edad, sexo y antropometría: trátalos como datos personales.
- No publiques paquetes sin el consentimiento explícito de cada participante para compartir datos.

## Formato del paquete (resumen)

```
participant  code, sex, age, weight_kg, height_cm, skinfold_mm, sport, muscle, side
session      start, duration_s, activity, type, protocol{start,step,stageMin,stopAt}, simulated
device       name, model, serial, hw, fw, calibration{slotA,slotB: dark[4], power[4]}
streams.calc t_s, hhb_uM, hbo2_uM, smo2_frac, zone_fw, arrival_ms     (~4 Hz)
streams.raw  t_s, raw1a..raw4a, raw1b..raw4b, arrival_ms               (~4 Hz)
streams.hr   t_s, bpm
streams.rr   t_s, rr_ms
markers      t, stage, lac, vo2, ve, rer, rpe, note, smo2
derived      stats, threshold, dfa, dfa_thresholds, intervals, laps, analytics
```

`arrival_ms` es la hora de llegada de cada paquete Bluetooth (`performance.now()`). Permite medir el muestreo real y su irregularidad, que es clave para cualquier análisis espectral.
