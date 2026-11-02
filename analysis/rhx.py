"""Utilidades comunes para leer paquetes de investigación de ReadHumHex.

Esquema: readhumhex-research/1 (lo genera docs/index.html en modo investigación).
Uso: from rhx import load, calc_df, raw_df, rr_df, hr_df, markers_df
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA = "readhumhex-research/1"


def load(path: str | Path) -> dict:
    pkg = json.loads(Path(path).read_text(encoding="utf-8"))
    if pkg.get("schema") != SCHEMA:
        raise ValueError(f"{path}: esquema {pkg.get('schema')!r}, se esperaba {SCHEMA!r}")
    return pkg


def _df(stream: dict) -> pd.DataFrame:
    return pd.DataFrame(stream.get("rows", []), columns=stream["columns"])


def calc_df(pkg: dict) -> pd.DataFrame:
    """Datos calculados por el firmware a frecuencia completa (~4 Hz)."""
    df = _df(pkg["streams"]["calc"])
    if not df.empty:
        df["smo2"] = df["smo2_frac"] * 100
        df["thb_uM"] = df["hhb_uM"] + df["hbo2_uM"]
    return df


def raw_df(pkg: dict) -> pd.DataFrame:
    return _df(pkg["streams"]["raw"])


def rr_df(pkg: dict) -> pd.DataFrame:
    return _df(pkg["streams"]["rr"])


def hr_df(pkg: dict) -> pd.DataFrame:
    return _df(pkg["streams"]["hr"])


def markers_df(pkg: dict) -> pd.DataFrame:
    return pd.DataFrame(pkg.get("markers", []))


def time_axis(df, pkg: dict):
    """Tiempo en segundos para análisis espectral.

    Usa la hora de llegada de cada paquete (refleja el muestreo real del Hex).
    En sesiones simuladas o si la hora de llegada no es válida (paquetes con la
    misma marca), usa el tiempo de sesión t_s.
    """
    import numpy as _np
    if "arrival_ms" in df and not is_simulated(pkg):
        a = df["arrival_ms"].to_numpy(float)
        if len(a) > 2 and _np.median(_np.diff(a)) > 0:
            return (a - a[0]) / 1000, "llegada"
    t = df["t_s"].to_numpy(float)
    return t - t[0], "sesión"


def is_simulated(pkg: dict) -> bool:
    return bool(pkg["session"].get("simulated"))


def label(pkg: dict) -> str:
    s = pkg["session"]
    sim = " · SIMULADO" if is_simulated(pkg) else ""
    return f"{pkg['participant']['code']} · {s['start'][:16]} · {s['type']}{sim}"


def bilinear(x: np.ndarray, y: np.ndarray, min_seg: int) -> dict | None:
    """Ajuste de dos rectas con corte óptimo (mínimo error cuadrático total).

    Igual criterio que la app: devuelve la intersección de las rectas y el R²
    del modelo bilineal.
    """
    n = len(x)
    if n < 2 * min_seg + 2:
        return None
    best = None
    for k in range(min_seg, n - min_seg + 1):
        a = np.polyfit(x[:k], y[:k], 1)
        b = np.polyfit(x[k:], y[k:], 1)
        sse = np.sum((y[:k] - np.polyval(a, x[:k])) ** 2) + np.sum((y[k:] - np.polyval(b, x[k:])) ** 2)
        if best is None or sse < best[0]:
            best = (sse, k, a, b)
    sse, k, a, b = best
    sst = np.sum((y - y.mean()) ** 2)
    xi = (b[1] - a[1]) / (a[0] - b[0]) if a[0] != b[0] else x[k]
    if not (x[0] <= xi <= x[-1]):
        xi = x[k]
    return {"x": float(xi), "r2": float(1 - sse / sst) if sst > 0 else 0.0, "slope_a": float(a[0]), "slope_b": float(b[0]), "k": int(k)}


def dfa_a1(rr_ms: np.ndarray) -> float | None:
    """DFA-α1 (cajas de 4 a 16 latidos), con el mismo filtro de artefactos que la app."""
    clean = []
    for v in rr_ms:
        if v < 300 or v > 2000:
            continue
        if clean and abs(v - clean[-1]) / clean[-1] > 0.2:
            continue
        clean.append(v)
    x = np.asarray(clean, float)
    if len(x) < 80:
        return None
    y = np.cumsum(x - x.mean())
    ns, fs = [], []
    for n in range(4, 17):
        nb = len(y) // n
        if nb < 2:
            continue
        segs = y[: nb * n].reshape(nb, n)
        t = np.arange(n)
        res = []
        for seg in segs:
            c = np.polyfit(t, seg, 1)
            res.append(seg - np.polyval(c, t))
        ns.append(np.log(n))
        fs.append(np.log(np.sqrt(np.mean(np.concatenate(res) ** 2))))
    if len(ns) < 5:
        return None
    return float(np.polyfit(ns, fs, 1)[0])


def lactate_at(markers: pd.DataFrame, target: float, x_col: str = "t") -> float | None:
    """Interpola linealmente el valor de x_col en que el lactato cruza target (mmol/L)."""
    if markers.empty or "lac" not in markers:
        return None
    m = markers.dropna(subset=["lac"]).sort_values("t")
    for (_, a), (_, b) in zip(m.iterrows(), m.iloc[1:].iterrows()):
        if a["lac"] < target <= b["lac"]:
            f = (target - a["lac"]) / (b["lac"] - a["lac"])
            return float(a[x_col] + f * (b[x_col] - a[x_col]))
    return None
