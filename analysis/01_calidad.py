"""01 · Calidad de los datos de cada paquete.

Informa frecuencia real y regularidad (jitter) de CALC y RAW según la hora de
llegada, huecos, coherencia HbO2/tHb ≈ SmO2, cobertura de RR y artefactos.

Uso: python 01_calidad.py paquetes/*.json
"""
import sys

import numpy as np

import rhx


def timing(t_s: np.ndarray) -> dict:
    if len(t_s) < 3:
        return {"n": len(t_s)}
    d = np.diff(t_s)
    d = d[d > 0] if np.any(d > 0) else d
    return {
        "n": len(t_s),
        "hz": 1 / np.median(d),
        "jitter_ms": float(np.std(d) * 1000),
        "huecos_>1s": int(np.sum(d > 1.0)),
    }


def main(paths):
    for path in paths:
        pkg = rhx.load(path)
        print(f"\n== {rhx.label(pkg)}  ({path})")
        calc, raw, rr = rhx.calc_df(pkg), rhx.raw_df(pkg), rhx.rr_df(pkg)
        if not calc.empty:
            tt, src = rhx.time_axis(calc, pkg)
            t = timing(tt)
            coh = np.abs(calc["hbo2_uM"] / calc["thb_uM"] - calc["smo2_frac"])
            print(f"CALC  [{src}] n={t['n']}  {t.get('hz', 0):.2f} Hz  jitter {t.get('jitter_ms', 0):.0f} ms  huecos>1s {t.get('huecos_>1s', 0)}  "
                  f"incoherentes {int((coh > 0.025).sum())}")
            z = calc["zone_fw"].round().value_counts().sort_index()
            print("Zona firmware (muestras):", dict(z))
        else:
            print("CALC  sin datos (¿modo investigación desactivado?)")
        if not raw.empty:
            tt, src = rhx.time_axis(raw, pkg)
            t = timing(tt)
            sim = " (SIMULADO)" if pkg["streams"]["raw"].get("simulated") else ""
            print(f"RAW   [{src}] n={t['n']}  {t.get('hz', 0):.2f} Hz  jitter {t.get('jitter_ms', 0):.0f} ms{sim}")
            print("      Nyquist", f"{t.get('hz', 0) / 2 * 60:.0f} lpm", "→ FC por encima de ese valor se pliega (aliasing)")
        else:
            print("RAW   sin datos")
        if not rr.empty:
            v = rr["rr_ms"].to_numpy()
            art = np.mean(np.abs(np.diff(v)) / v[:-1] > 0.2) * 100 if len(v) > 1 else 0
            print(f"RR    n={len(v)}  FC media {60000 / v.mean():.0f} lpm  artefactos {art:.1f} %")
        else:
            print("RR    sin datos (la banda no envía RR o no se conectó)")
        m = rhx.markers_df(pkg)
        print("Marcadores:", len(m), "· con lactato:", int(m["lac"].notna().sum()) if "lac" in m else 0)


if __name__ == "__main__":
    main(sys.argv[1:] or ["sample/demo_P001_umbral.json"])
