"""03 · Métodos de umbral frente al lactato de referencia.

Por cada prueba incremental compara, en tiempo (s) y en FC (lpm):
  · referencia: lactato 2 y 4 mmol/L, interpolado desde los marcadores
  · bilineal SmO2–tiempo (método de la app)
  · bilineal SmO2–FC (independiente de la actividad, experimental)
  · bilineal HHb–tiempo
  · inicio de zona roja sostenida ≥30 s (zona del firmware)
  · DFA-α1 = 0,75 y 0,5 (desde RR)
Con 2 o más pruebas informa sesgo y límites de acuerdo de Bland–Altman.

Uso: python 03_umbrales_vs_referencia.py paquetes/*.json  [--csv salida.csv]
"""
import sys

import numpy as np
import pandas as pd

import rhx


def per_second(pkg):
    calc = rhx.calc_df(pkg)
    calc["sec"] = calc["t_s"].round().astype(int)
    g = calc.groupby("sec").agg(smo2=("smo2", "mean"), hhb=("hhb_uM", "mean"), zone=("zone_fw", "last")).reset_index()
    hr = rhx.hr_df(pkg)
    if not hr.empty:
        hr["sec"] = hr["t_s"].round().astype(int)
        g = g.merge(hr.groupby("sec")["bpm"].mean().rename("hr").reset_index(), on="sec", how="left")
        g["hr"] = g["hr"].interpolate(limit_direction="both")
    else:
        g["hr"] = np.nan
    return g


def hr_at(g, t):
    if t is None or g["hr"].isna().all():
        return None
    return float(np.interp(t, g["sec"], g["hr"]))


def methods(pkg):
    p = pkg["session"]["protocol"] or {}
    end = p.get("stopAt") or pkg["session"]["duration_s"]
    stage = (p.get("stageMin") or 3) * 60
    g = per_second(pkg)
    g = g[g["sec"] <= end]
    x = g["sec"].to_numpy(float)
    out = {}
    f = rhx.bilinear(x, g["smo2"].to_numpy(), max(20, stage // 2))
    out["bilineal_SmO2_t"] = f["x"] if f and f["r2"] >= 0.95 and f["slope_b"] < f["slope_a"] else None
    f = rhx.bilinear(x, g["hhb"].to_numpy(), max(20, stage // 2))
    out["bilineal_HHb_t"] = f["x"] if f and f["slope_b"] > f["slope_a"] else None
    if g["hr"].notna().sum() > 60:
        h = g.dropna(subset=["hr"]).sort_values("hr")
        hb = h.groupby(h["hr"].round())["smo2"].mean()
        if len(hb) > 20:
            f = rhx.bilinear(hb.index.to_numpy(float), hb.to_numpy(), 8)
            out["bilineal_SmO2_FC_lpm"] = f["x"] if f and f["slope_b"] < f["slope_a"] else None
    red, start = None, None
    for s, z in zip(g["sec"], g["zone"].round()):
        if z == 5:
            start = s if start is None else start
            if s - start >= 30:
                red = float(start)
                break
        else:
            start = None
    out["inicio_zona_roja_t"] = red
    rr = rhx.rr_df(pkg)
    if not rr.empty:
        pts = []
        for t0 in range(120, int(end) + 1, 15):
            a = rhx.dfa_a1(rr.loc[(rr["t_s"] > t0 - 120) & (rr["t_s"] <= t0), "rr_ms"].to_numpy())
            h = hr_at(g, t0)
            if a is not None and h is not None and 0.25 < a < 1.3:
                pts.append((h, a))
        if len(pts) >= 8:
            hh, aa = np.array(pts).T
            k, c = np.polyfit(hh, aa, 1)
            if k < 0:
                out["DFA_a1_0.75_lpm"] = (0.75 - c) / k
                out["DFA_a1_0.50_lpm"] = (0.50 - c) / k
    m = rhx.markers_df(pkg)
    out["ref_lac2_t"] = rhx.lactate_at(m, 2.0)
    out["ref_lac4_t"] = rhx.lactate_at(m, 4.0)
    for key in ("bilineal_SmO2_t", "bilineal_HHb_t", "inicio_zona_roja_t", "ref_lac2_t", "ref_lac4_t"):
        out[key.replace("_t", "_lpm")] = hr_at(g, out.get(key))
    return out


def bland_altman(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    d = d[~np.isnan(d)]
    if len(d) < 2:
        return None
    return d.mean(), d.mean() - 1.96 * d.std(ddof=1), d.mean() + 1.96 * d.std(ddof=1), len(d)


def main(args):
    csv = None
    if "--csv" in args:
        i = args.index("--csv")
        csv = args[i + 1]
        args = args[:i] + args[i + 2:]
    rows = []
    for path in args or ["sample/demo_P001_umbral.json"]:
        pkg = rhx.load(path)
        if pkg["session"]["type"] != "incremental":
            continue
        r = methods(pkg)
        r["sesion"] = rhx.label(pkg)
        rows.append(r)
    if not rows:
        print("No hay pruebas incrementales.")
        return
    df = pd.DataFrame(rows).set_index("sesion")
    pd.set_option("display.width", 200)
    print(df.T.round(1))
    if csv:
        df.to_csv(csv)
    print("\nAcuerdo con lactato 4 mmol/L (FC, lpm): sesgo [LoA 95 %] n")
    for col in ("bilineal_SmO2_lpm", "bilineal_SmO2_FC_lpm", "bilineal_HHb_lpm", "inicio_zona_roja_lpm", "DFA_a1_0.50_lpm"):
        if col in df and "ref_lac4_lpm" in df:
            ba = bland_altman(df[col], df["ref_lac4_lpm"])
            print(f"  {col:<24}", "insuficiente (<2 pruebas)" if ba is None else f"{ba[0]:+.1f} [{ba[1]:+.1f}; {ba[2]:+.1f}] n={ba[3]}")
    print("\nAcuerdo con lactato 2 mmol/L (FC, lpm):")
    for col in ("DFA_a1_0.75_lpm",):
        if col in df and "ref_lac2_lpm" in df:
            ba = bland_altman(df[col], df["ref_lac2_lpm"])
            print(f"  {col:<24}", "insuficiente (<2 pruebas)" if ba is None else f"{ba[0]:+.1f} [{ba[1]:+.1f}; {ba[2]:+.1f}] n={ba[3]}")


if __name__ == "__main__":
    main(sys.argv[1:])
