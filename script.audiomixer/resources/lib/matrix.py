# -*- coding: utf-8 -*-
"""
Matriz de downmix 5.1 -> 2.0.

Representamos la mezcla como dos filas (una para L, otra para R), cada una
con un coeficiente por canal de origen: L, R, C, LFE, SL, SR.

Coeficientes "de fabrica" (downmix estandar ATSC):
    L_out = 1.0*L + 0.0*R + 0.707*C + 0.707*LFE + 0.707*SL + 0.0*SR
    R_out = 0.0*L + 1.0*R + 0.707*C + 0.707*LFE + 0.0*SL  + 0.707*SR
"""

CHANNELS = ["L", "R", "C", "LFE", "SL", "SR"]

BASE_MATRIX = {
    "L": {"L": 1.0, "R": 0.0, "C": 0.707, "LFE": 0.707, "SL": 0.707, "SR": 0.0},
    "R": {"L": 0.0, "R": 1.0, "C": 0.707, "LFE": 0.707, "SL": 0.0,  "SR": 0.707},
}

# Agrupacion del modo simple: cada grupo son celdas (salida, canal_origen)
# que se mueven juntas con un unico fader.
SIMPLE_GROUPS = {
    "lr":       [("L", "L"), ("R", "R")],
    "center":   [("L", "C"), ("R", "C")],
    "lfe":      [("L", "LFE"), ("R", "LFE")],
    "surround": [("L", "SL"), ("R", "SR")],
}

SIMPLE_LABELS = {
    "lr": "Frontales L/R",
    "center": "Central (dialogos)",
    "lfe": "LFE (subwoofer)",
    "surround": "Surround SL/SR",
}

ADVANCED_LABELS = {
    ("L", "L"): "L -> L", ("L", "R"): "R -> L", ("L", "C"): "C -> L",
    ("L", "LFE"): "LFE -> L", ("L", "SL"): "SL -> L", ("L", "SR"): "SR -> L",
    ("R", "L"): "L -> R", ("R", "R"): "R -> R", ("R", "C"): "C -> R",
    ("R", "LFE"): "LFE -> R", ("R", "SL"): "SL -> R", ("R", "SR"): "SR -> R",
}

MAX_FACTOR = 2.0  # 100% del slider = doble de ganancia


def simple_percent_to_factor(percent):
    """50% del slider = factor 1.0 (sin cambio sobre el valor de fabrica)."""
    return (percent / 50.0)


def simple_factor_to_percent(factor):
    return max(0, min(100, round(factor * 50.0)))


def advanced_percent_to_coeff(percent):
    """El slider representa directamente el coeficiente, de 0.0 a MAX_FACTOR."""
    return (percent / 100.0) * MAX_FACTOR


def advanced_coeff_to_percent(coeff):
    return max(0, min(100, round((coeff / MAX_FACTOR) * 100.0)))


def build_matrix_from_simple(group_percents):
    """group_percents: dict {'lr':50,'center':50,'lfe':50,'surround':50}"""
    matrix = {out: dict(BASE_MATRIX[out]) for out in BASE_MATRIX}
    for group, cells in SIMPLE_GROUPS.items():
        factor = simple_percent_to_factor(group_percents.get(group, 50))
        for out, ch in cells:
            matrix[out][ch] = BASE_MATRIX[out][ch] * factor
    return matrix


def build_matrix_from_advanced(cell_percents):
    """cell_percents: dict {(out,ch): percent} para las 12 celdas."""
    matrix = {"L": {}, "R": {}}
    for out in ("L", "R"):
        for ch in CHANNELS:
            percent = cell_percents.get((out, ch), advanced_coeff_to_percent(BASE_MATRIX[out][ch]))
            matrix[out][ch] = advanced_percent_to_coeff(percent)
    return matrix


def default_advanced_percents():
    return {(out, ch): advanced_coeff_to_percent(BASE_MATRIX[out][ch])
            for out in ("L", "R") for ch in CHANNELS}


def matrix_to_copy_line(matrix, precision=4):
    """Genera la linea 'Copy: L=... R=...' de Equalizer APO a partir de la matriz."""
    parts = []
    for out in ("L", "R"):
        terms = []
        for ch in CHANNELS:
            coeff = matrix[out][ch]
            if abs(coeff) < 1e-4:
                continue
            terms.append("%.*f*%s" % (precision, coeff, ch))
        expr = "+".join(terms) if terms else "0*L"
        parts.append("%s=%s" % (out, expr))
    return "Copy: " + " ".join(parts)
