"""04 · ¿Contiene la señal cruda del Hex el pulso cardíaco?

Experimento de factibilidad. Usa un tramo en REPOSO (sentado, quieto) con la
banda de FC conectada. Para cada canal RAW:
  1. usa la hora de llegada de cada paquete (no un reloj ideal) y calcula el
     espectro con Lomb–Scargle, que tolera muestreo irregular;
  2. busca el pico en 0,67–2 Hz (40–120 lpm, bajo Nyquist a ~4 Hz);
  3. compara con la FC de la banda y calcula la razón señal/ruido del pico.

Criterio: el pulso está presente si en ≥2 canales el pico cae a ±5 lpm de la
banda y supera 3 veces la mediana del espectro. Sobre ~120 lpm la FC se
pliega (aliasing) y este método no sirve sin información adicional.

Uso: python 04_fc_desde_raw.py paquete.json [--desde 30 --hasta 150]
"""
import sys

import numpy as np
from scipy.signal import detrend, lombscargle

import rhx


def main(args):
    path = args[0] if args else "sample/demo_P001_umbral.json"
    t0 = float(args[args.index("--desde") + 1]) if "--desde" in args else 30.0
    t1 = float(args[args.index("--hasta") + 1]) if "--hasta" in args else 150.0
    pkg = rhx.load(path)
    raw, hr = rhx.raw_df(pkg), rhx.hr_df(pkg)
    if raw.empty:
        print("El paquete no tiene RAW. Activa el modo investigación y conecta el Hex.")
        return
    if pkg["streams"]["raw"].get("simulated"):
        print("AVISO: RAW SIMULADO (demo). Sirve para probar el script, no como evidencia.")
    seg = raw[(raw["t_s"] >= t0) & (raw["t_s"] <= t1)]
    if len(seg) < 120:
        print(f"Tramo muy corto ({len(seg)} muestras). Usa ≥2 min en reposo.")
        return
    t, src = rhx.time_axis(seg, pkg)
    fs = 1 / np.median(np.diff(t)[np.diff(t) > 0])
    ref = hr[(hr["t_s"] >= t0) & (hr["t_s"] <= t1)]["bpm"].mean() if not hr.empty else np.nan
    print(f"Tramo {t0:.0f}–{t1:.0f} s · tiempo de {src} · {len(seg)} muestras · fs ≈ {fs:.2f} Hz · Nyquist ≈ {fs / 2 * 60:.0f} lpm · FC banda {ref:.0f} lpm")
    if ref > fs / 2 * 60:
        print("La FC de referencia supera Nyquist: el pico aparecería plegado. Repite en reposo.")
    freqs = np.linspace(0.67, min(2.0, fs / 2 - 0.05), 600)
    hits = 0
    for ch in [c for c in seg.columns if c.startswith("raw")]:
        y = detrend(seg[ch].to_numpy(float))
        y = (y - y.mean()) / (y.std() or 1)
        p = lombscargle(t, y, 2 * np.pi * freqs, normalize=True)
        k = int(np.argmax(p))
        bpm, snr = freqs[k] * 60, p[k] / np.median(p)
        ok = abs(bpm - ref) <= 5 and snr >= 3
        hits += ok
        print(f"  {ch}: pico {bpm:5.1f} lpm · SNR {snr:4.1f} · {'COINCIDE' if ok else '—'}")
    print("\nResultado:", "pulso detectable en reposo" if hits >= 2 else "sin evidencia de pulso utilizable", f"({hits}/8 canales)")


if __name__ == "__main__":
    main(sys.argv[1:])
