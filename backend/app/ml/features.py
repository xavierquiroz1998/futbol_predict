"""
Feature engineering para predicción de partidos de fútbol.

Features incluidos:
- Forma reciente (últimos 5 partidos): victorias, empates, derrotas, goles, puntos
- Racha actual: partidos consecutivos ganando/sin perder/perdiendo
- Tendencia de goles: over/under 2.5, ambos anotan (BTTS)
- Rendimiento local/visitante: win rate y goles en esa condición
- Head-to-head: historial de enfrentamientos directos
- Diferencial de fuerza: diferencia de puntos y goles entre equipos
- Forma ampliada (últimos 10 partidos) para tendencia a largo plazo
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.partido import Partido


def obtener_partidos_como_df(db: Session) -> pd.DataFrame:
    """Obtiene todos los partidos finalizados de la BD como DataFrame."""
    partidos = db.query(Partido).filter(Partido.finalizado == True).all()  # noqa: E712

    if not partidos:
        return pd.DataFrame()

    data = []
    for p in partidos:
        data.append({
            "api_id": p.api_id,
            "fecha": p.fecha,
            "liga": p.liga_nombre,
            "local_id": p.equipo_local_api_id,
            "local_nombre": p.equipo_local_nombre,
            "visitante_id": p.equipo_visitante_api_id,
            "visitante_nombre": p.equipo_visitante_nombre,
            "goles_local": p.goles_local,
            "goles_visitante": p.goles_visitante,
        })

    df = pd.DataFrame(data)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = df.sort_values("fecha").reset_index(drop=True)
    return df


def calcular_resultado(row: pd.Series) -> str:
    if row["goles_local"] > row["goles_visitante"]:
        return "local"
    elif row["goles_local"] < row["goles_visitante"]:
        return "visitante"
    return "empate"


def _forma_reciente(df: pd.DataFrame, equipo_id: int, fecha: datetime, n: int = 5) -> dict:
    """Forma reciente: victorias, empates, derrotas, goles, puntos en últimos N partidos."""
    partidos_previos = df[
        ((df["local_id"] == equipo_id) | (df["visitante_id"] == equipo_id))
        & (df["fecha"] < fecha)
    ].tail(n)

    if len(partidos_previos) == 0:
        return {
            "victorias": 0, "empates": 0, "derrotas": 0,
            "goles_favor": 0, "goles_contra": 0, "puntos": 0,
            "partidos": 0, "clean_sheets": 0,
        }

    victorias = empates = derrotas = gf = gc = clean = 0

    for _, row in partidos_previos.iterrows():
        if row["local_id"] == equipo_id:
            gf += row["goles_local"]
            gc += row["goles_visitante"]
            if row["goles_visitante"] == 0:
                clean += 1
            if row["goles_local"] > row["goles_visitante"]:
                victorias += 1
            elif row["goles_local"] == row["goles_visitante"]:
                empates += 1
            else:
                derrotas += 1
        else:
            gf += row["goles_visitante"]
            gc += row["goles_local"]
            if row["goles_local"] == 0:
                clean += 1
            if row["goles_visitante"] > row["goles_local"]:
                victorias += 1
            elif row["goles_visitante"] == row["goles_local"]:
                empates += 1
            else:
                derrotas += 1

    total = len(partidos_previos)
    return {
        "victorias": victorias / total,
        "empates": empates / total,
        "derrotas": derrotas / total,
        "goles_favor": gf / total,
        "goles_contra": gc / total,
        "puntos": (victorias * 3 + empates) / total,
        "partidos": total,
        "clean_sheets": clean / total,
    }


def _racha_actual(df: pd.DataFrame, equipo_id: int, fecha: datetime) -> dict:
    """Calcula rachas: partidos consecutivos ganando, sin perder, perdiendo."""
    partidos = df[
        ((df["local_id"] == equipo_id) | (df["visitante_id"] == equipo_id))
        & (df["fecha"] < fecha)
    ].tail(15)

    if len(partidos) == 0:
        return {"racha_victorias": 0, "racha_sin_perder": 0, "racha_derrotas": 0, "racha_goles": 0}

    racha_v = racha_sp = racha_d = racha_gol = 0

    for _, row in partidos.iloc[::-1].iterrows():
        es_local = row["local_id"] == equipo_id
        if es_local:
            gf, gc = row["goles_local"], row["goles_visitante"]
        else:
            gf, gc = row["goles_visitante"], row["goles_local"]

        gano = gf > gc
        empato = gf == gc
        perdio = gf < gc

        if gano and racha_d == 0:
            racha_v += 1
        if not perdio and racha_d == 0:
            racha_sp += 1
        if perdio and racha_v == 0:
            racha_d += 1
        if gf > 0:
            racha_gol += 1
        else:
            break

        if (gano and racha_d > 0) or (perdio and racha_v > 0):
            break

    return {
        "racha_victorias": racha_v,
        "racha_sin_perder": racha_sp,
        "racha_derrotas": racha_d,
        "racha_goles": racha_gol,
    }


def _tendencia_goles(df: pd.DataFrame, equipo_id: int, fecha: datetime, n: int = 10) -> dict:
    """Tendencia de goles: over/under 2.5, BTTS, promedio total."""
    partidos = df[
        ((df["local_id"] == equipo_id) | (df["visitante_id"] == equipo_id))
        & (df["fecha"] < fecha)
    ].tail(n)

    if len(partidos) == 0:
        return {"over_2_5": 0, "btts": 0, "goles_total_prom": 0}

    over = 0
    btts = 0
    total_goles = 0

    for _, row in partidos.iterrows():
        gl = row["goles_local"]
        gv = row["goles_visitante"]
        total = gl + gv
        total_goles += total

        if total > 2.5:
            over += 1
        if gl > 0 and gv > 0:
            btts += 1

    n_partidos = len(partidos)
    return {
        "over_2_5": over / n_partidos,
        "btts": btts / n_partidos,
        "goles_total_prom": total_goles / n_partidos,
    }


def _rendimiento_local_visitante(
    df: pd.DataFrame, equipo_id: int, fecha: datetime, es_local: bool, n: int = 10
) -> dict:
    col = "local_id" if es_local else "visitante_id"
    partidos = df[(df[col] == equipo_id) & (df["fecha"] < fecha)].tail(n)

    if len(partidos) == 0:
        return {"win_rate_condicion": 0, "goles_prom_condicion": 0, "gc_prom_condicion": 0}

    wins = goles = gc = 0
    for _, row in partidos.iterrows():
        if es_local:
            goles += row["goles_local"]
            gc += row["goles_visitante"]
            if row["goles_local"] > row["goles_visitante"]:
                wins += 1
        else:
            goles += row["goles_visitante"]
            gc += row["goles_local"]
            if row["goles_visitante"] > row["goles_local"]:
                wins += 1

    total = len(partidos)
    return {
        "win_rate_condicion": wins / total,
        "goles_prom_condicion": goles / total,
        "gc_prom_condicion": gc / total,
    }


def _head_to_head(
    df: pd.DataFrame, local_id: int, visitante_id: int, fecha: datetime, n: int = 5
) -> dict:
    h2h = df[
        (
            ((df["local_id"] == local_id) & (df["visitante_id"] == visitante_id))
            | ((df["local_id"] == visitante_id) & (df["visitante_id"] == local_id))
        )
        & (df["fecha"] < fecha)
    ].tail(n)

    if len(h2h) == 0:
        return {"h2h_win_local": 0, "h2h_empates": 0, "h2h_win_visitante": 0, "h2h_goles_prom": 0}

    w_local = w_visitante = emp = total_goles = 0
    for _, row in h2h.iterrows():
        total_goles += row["goles_local"] + row["goles_visitante"]
        if row["goles_local"] > row["goles_visitante"]:
            if row["local_id"] == local_id:
                w_local += 1
            else:
                w_visitante += 1
        elif row["goles_local"] < row["goles_visitante"]:
            if row["visitante_id"] == local_id:
                w_local += 1
            else:
                w_visitante += 1
        else:
            emp += 1

    total = len(h2h)
    return {
        "h2h_win_local": w_local / total,
        "h2h_empates": emp / total,
        "h2h_win_visitante": w_visitante / total,
        "h2h_goles_prom": total_goles / total,
    }


def generar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Genera el dataset completo de features para entrenamiento."""
    rows = []

    for idx, partido in df.iterrows():
        if idx < 30:
            continue

        local_id = partido["local_id"]
        visitante_id = partido["visitante_id"]
        fecha = partido["fecha"]

        # Forma reciente 5 partidos
        forma_local_5 = _forma_reciente(df, local_id, fecha, n=5)
        forma_visitante_5 = _forma_reciente(df, visitante_id, fecha, n=5)

        if forma_local_5["partidos"] < 3 or forma_visitante_5["partidos"] < 3:
            continue

        # Forma ampliada 10 partidos
        forma_local_10 = _forma_reciente(df, local_id, fecha, n=10)
        forma_visitante_10 = _forma_reciente(df, visitante_id, fecha, n=10)

        # Rachas
        racha_local = _racha_actual(df, local_id, fecha)
        racha_visitante = _racha_actual(df, visitante_id, fecha)

        # Tendencia goles
        tend_local = _tendencia_goles(df, local_id, fecha)
        tend_visitante = _tendencia_goles(df, visitante_id, fecha)

        # Rendimiento local/visitante
        rend_local = _rendimiento_local_visitante(df, local_id, fecha, es_local=True)
        rend_visitante = _rendimiento_local_visitante(df, visitante_id, fecha, es_local=False)

        # Head to head
        h2h = _head_to_head(df, local_id, visitante_id, fecha)

        resultado = calcular_resultado(partido)

        row = {
            "api_id": partido["api_id"],

            # === Forma reciente (5 partidos) ===
            "local_victorias_5": forma_local_5["victorias"],
            "local_empates_5": forma_local_5["empates"],
            "local_derrotas_5": forma_local_5["derrotas"],
            "local_gf_prom_5": forma_local_5["goles_favor"],
            "local_gc_prom_5": forma_local_5["goles_contra"],
            "local_puntos_5": forma_local_5["puntos"],
            "local_clean_sheets_5": forma_local_5["clean_sheets"],

            "visitante_victorias_5": forma_visitante_5["victorias"],
            "visitante_empates_5": forma_visitante_5["empates"],
            "visitante_derrotas_5": forma_visitante_5["derrotas"],
            "visitante_gf_prom_5": forma_visitante_5["goles_favor"],
            "visitante_gc_prom_5": forma_visitante_5["goles_contra"],
            "visitante_puntos_5": forma_visitante_5["puntos"],
            "visitante_clean_sheets_5": forma_visitante_5["clean_sheets"],

            # === Forma ampliada (10 partidos) ===
            "local_puntos_10": forma_local_10["puntos"],
            "local_gf_prom_10": forma_local_10["goles_favor"],
            "local_gc_prom_10": forma_local_10["goles_contra"],
            "visitante_puntos_10": forma_visitante_10["puntos"],
            "visitante_gf_prom_10": forma_visitante_10["goles_favor"],
            "visitante_gc_prom_10": forma_visitante_10["goles_contra"],

            # === Rachas ===
            "local_racha_victorias": racha_local["racha_victorias"],
            "local_racha_sin_perder": racha_local["racha_sin_perder"],
            "local_racha_derrotas": racha_local["racha_derrotas"],
            "local_racha_goles": racha_local["racha_goles"],
            "visitante_racha_victorias": racha_visitante["racha_victorias"],
            "visitante_racha_sin_perder": racha_visitante["racha_sin_perder"],
            "visitante_racha_derrotas": racha_visitante["racha_derrotas"],
            "visitante_racha_goles": racha_visitante["racha_goles"],

            # === Tendencia goles ===
            "local_over_2_5": tend_local["over_2_5"],
            "local_btts": tend_local["btts"],
            "local_goles_total_prom": tend_local["goles_total_prom"],
            "visitante_over_2_5": tend_visitante["over_2_5"],
            "visitante_btts": tend_visitante["btts"],
            "visitante_goles_total_prom": tend_visitante["goles_total_prom"],

            # === Rendimiento local/visitante ===
            "local_win_rate_casa": rend_local["win_rate_condicion"],
            "local_goles_prom_casa": rend_local["goles_prom_condicion"],
            "local_gc_prom_casa": rend_local["gc_prom_condicion"],
            "visitante_win_rate_fuera": rend_visitante["win_rate_condicion"],
            "visitante_goles_prom_fuera": rend_visitante["goles_prom_condicion"],
            "visitante_gc_prom_fuera": rend_visitante["gc_prom_condicion"],

            # === Head to head ===
            "h2h_win_local": h2h["h2h_win_local"],
            "h2h_empates": h2h["h2h_empates"],
            "h2h_win_visitante": h2h["h2h_win_visitante"],
            "h2h_goles_prom": h2h["h2h_goles_prom"],

            # === Diferenciales (fuerza relativa) ===
            "diff_puntos_5": forma_local_5["puntos"] - forma_visitante_5["puntos"],
            "diff_puntos_10": forma_local_10["puntos"] - forma_visitante_10["puntos"],
            "diff_gf": forma_local_5["goles_favor"] - forma_visitante_5["goles_favor"],
            "diff_gc": forma_local_5["goles_contra"] - forma_visitante_5["goles_contra"],
            "diff_racha": racha_local["racha_victorias"] - racha_visitante["racha_victorias"],

            # Target
            "resultado": resultado,
        }
        rows.append(row)

    return pd.DataFrame(rows)


FEATURE_COLUMNS = [
    # Forma 5
    "local_victorias_5", "local_empates_5", "local_derrotas_5",
    "local_gf_prom_5", "local_gc_prom_5", "local_puntos_5", "local_clean_sheets_5",
    "visitante_victorias_5", "visitante_empates_5", "visitante_derrotas_5",
    "visitante_gf_prom_5", "visitante_gc_prom_5", "visitante_puntos_5", "visitante_clean_sheets_5",
    # Forma 10
    "local_puntos_10", "local_gf_prom_10", "local_gc_prom_10",
    "visitante_puntos_10", "visitante_gf_prom_10", "visitante_gc_prom_10",
    # Rachas
    "local_racha_victorias", "local_racha_sin_perder", "local_racha_derrotas", "local_racha_goles",
    "visitante_racha_victorias", "visitante_racha_sin_perder", "visitante_racha_derrotas", "visitante_racha_goles",
    # Tendencia goles
    "local_over_2_5", "local_btts", "local_goles_total_prom",
    "visitante_over_2_5", "visitante_btts", "visitante_goles_total_prom",
    # Rendimiento local/visitante
    "local_win_rate_casa", "local_goles_prom_casa", "local_gc_prom_casa",
    "visitante_win_rate_fuera", "visitante_goles_prom_fuera", "visitante_gc_prom_fuera",
    # H2H
    "h2h_win_local", "h2h_empates", "h2h_win_visitante", "h2h_goles_prom",
    # Diferenciales
    "diff_puntos_5", "diff_puntos_10", "diff_gf", "diff_gc", "diff_racha",
]
