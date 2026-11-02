"""02 · Modelo abierto de la zona del firmware.

El firmware del Hex envía su zona (0–5) junto con HHb, HbO2 y SmO2, pero su
algoritmo no es público. Este script ajusta un modelo interpretable que
reproduce esa zona a partir de rasgos de las señales (nivel relativo al
basal, pendientes en ventanas de 10/30/60 s, tHb), siguiendo lo que describe
la patente US10799162B2: retroalimentación según si la señal sube, se
estabiliza o baja en ventanas de tiempo.

Valida con grupos (cada sesión es un grupo) para no sobreestimar el acierto.
Uso: python 02_modelo_zonas.py paquetes/*.json
"""
import sys

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score, confusion_matrix
from sklearn.model_selection import GroupKFold
from sklearn.tree import DecisionTreeClassifier, export_text

import rhx

WINDOWS = (10, 30, 60)


def features(calc: pd.DataFrame) -> pd.DataFrame:
    df = calc.copy()
    df["sec"] = df["t_s"].round().astype(int)
    g = df.groupby("sec").agg(smo2=("smo2", "mean"), hhb=("hhb_uM", "mean"), hbo2=("hbo2_uM", "mean"), thb=("thb_uM", "mean"), zone=("zone_fw", "last")).reset_index()
    base = g.loc[g["sec"] <= 60, ["smo2", "hhb", "hbo2", "thb"]].mean()
    for col in ("smo2", "hhb", "hbo2", "thb"):
        g[f"d_{col}"] = g[col] - base[col]
        for w in WINDOWS:
            g[f"s{w}_{col}"] = g[col].diff(w) / w
    g["zone"] = g["zone"].round().astype(int)
    return g.dropna()


def main(paths):
    frames = []
    for i, path in enumerate(paths):
        pkg = rhx.load(path)
        calc = rhx.calc_df(pkg)
        if calc.empty:
            continue
        f = features(calc)
        f["grupo"] = i
        f["sim"] = rhx.is_simulated(pkg)
        frames.append(f)
    if not frames:
        print("Sin datos CALC.")
        return
    data = pd.concat(frames, ignore_index=True)
    data = data[data["zone"] >= 2]
    if data["sim"].any():
        print("AVISO: hay sesiones simuladas; la zona demo NO es la del firmware real.")
    X = data.drop(columns=["zone", "grupo", "sim", "sec"])
    y = data["zone"].to_numpy()
    groups = data["grupo"].to_numpy()
    n_groups = len(set(groups))
    model = DecisionTreeClassifier(max_depth=4, min_samples_leaf=20, random_state=0)
    if n_groups >= 3:
        pred = np.zeros_like(y)
        for tr, te in GroupKFold(n_splits=min(5, n_groups)).split(X, y, groups):
            model.fit(X.iloc[tr], y[tr])
            pred[te] = model.predict(X.iloc[te])
        print(f"Validación por sesión ({n_groups} sesiones): acierto {np.mean(pred == y):.1%} · kappa {cohen_kappa_score(y, pred):.2f}")
        print("Matriz de confusión (filas real 2–5, columnas predicha):")
        print(confusion_matrix(y, pred, labels=[2, 3, 4, 5]))
    else:
        print(f"Solo {n_groups} sesión(es): se ajusta sin validación cruzada (acierto optimista).")
    model.fit(X, y)
    print(f"Acierto en entrenamiento: {np.mean(model.predict(X) == y):.1%}")
    print("\nReglas del modelo (legibles, para documentar el algoritmo abierto):")
    print(export_text(model, feature_names=list(X.columns), decimals=3))


if __name__ == "__main__":
    main(sys.argv[1:] or ["sample/demo_P001_umbral.json"])
