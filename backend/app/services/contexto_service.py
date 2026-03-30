"""
Genera contexto estadístico detallado para un partido.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.ml.features import (
    _forma_reciente,
    _racha_actual,
    _rendimiento_local_visitante,
    _tendencia_goles,
    obtener_partidos_como_df,
)
from app.models.partido import Partido
from app.schemas.partido import (
    ContextoPrediccionResponse,
    EstadisticasEquipoResponse,
)


def _ultimos_5_str(df, equipo_id, fecha) -> str:
    """Genera string tipo 'VVEDV' con últimos 5 resultados."""
    partidos = df[
        ((df["local_id"] == equipo_id) | (df["visitante_id"] == equipo_id))
        & (df["fecha"] < fecha)
    ].tail(5)

    resultado = ""
    for _, row in partidos.iterrows():
        es_local = row["local_id"] == equipo_id
        if es_local:
            gf, gc = row["goles_local"], row["goles_visitante"]
        else:
            gf, gc = row["goles_visitante"], row["goles_local"]

        if gf > gc:
            resultado += "V"
        elif gf == gc:
            resultado += "E"
        else:
            resultado += "D"

    return resultado


def _h2h_detalle(df, local_id, visitante_id, fecha, n=5):
    """Obtiene detalle de enfrentamientos directos."""
    h2h = df[
        (
            ((df["local_id"] == local_id) & (df["visitante_id"] == visitante_id))
            | ((df["local_id"] == visitante_id) & (df["visitante_id"] == local_id))
        )
        & (df["fecha"] < fecha)
    ].tail(n)

    wins_local = wins_visitante = empates = 0
    total_goles = 0
    ultimos = []

    for _, row in h2h.iterrows():
        gl = row["goles_local"]
        gv = row["goles_visitante"]
        total_goles += gl + gv
        local_nombre = row["local_nombre"]
        visitante_nombre = row["visitante_nombre"]

        if gl > gv:
            if row["local_id"] == local_id:
                wins_local += 1
            else:
                wins_visitante += 1
            ultimos.append(f"{local_nombre} {gl}-{gv} {visitante_nombre}")
        elif gl < gv:
            if row["visitante_id"] == local_id:
                wins_local += 1
            else:
                wins_visitante += 1
            ultimos.append(f"{local_nombre} {gl}-{gv} {visitante_nombre}")
        else:
            empates += 1
            ultimos.append(f"{local_nombre} {gl}-{gv} {visitante_nombre}")

    total = len(h2h)
    return {
        "total": total,
        "wins_local": wins_local,
        "empates": empates,
        "wins_visitante": wins_visitante,
        "goles_prom": total_goles / total if total > 0 else 0,
        "ultimos": list(reversed(ultimos)),  # más reciente primero
    }


def generar_contexto(db: Session, partido: Partido) -> ContextoPrediccionResponse | None:
    """Genera contexto estadístico completo para un partido."""
    df = obtener_partidos_como_df(db)
    if df.empty:
        return None

    local_id = partido.equipo_local_api_id
    visitante_id = partido.equipo_visitante_api_id
    fecha = partido.fecha

    # Estadísticas local
    forma_local = _forma_reciente(df, local_id, fecha, n=5)
    racha_local = _racha_actual(df, local_id, fecha)
    tend_local = _tendencia_goles(df, local_id, fecha)
    rend_local = _rendimiento_local_visitante(df, local_id, fecha, es_local=True)
    ultimos_local = _ultimos_5_str(df, local_id, fecha)

    # Estadísticas visitante
    forma_visitante = _forma_reciente(df, visitante_id, fecha, n=5)
    racha_visitante = _racha_actual(df, visitante_id, fecha)
    tend_visitante = _tendencia_goles(df, visitante_id, fecha)
    rend_visitante = _rendimiento_local_visitante(df, visitante_id, fecha, es_local=False)
    ultimos_visitante = _ultimos_5_str(df, visitante_id, fecha)

    # H2H
    h2h = _h2h_detalle(df, local_id, visitante_id, fecha)

    n5 = forma_local["partidos"]
    local_stats = EstadisticasEquipoResponse(
        nombre=partido.equipo_local_nombre,
        ultimos_5=ultimos_local,
        victorias_5=int(forma_local["victorias"] * n5) if n5 > 0 else 0,
        empates_5=int(forma_local["empates"] * n5) if n5 > 0 else 0,
        derrotas_5=int(forma_local["derrotas"] * n5) if n5 > 0 else 0,
        goles_favor_prom=round(forma_local["goles_favor"], 2),
        goles_contra_prom=round(forma_local["goles_contra"], 2),
        clean_sheets_5=int(forma_local["clean_sheets"] * n5) if n5 > 0 else 0,
        racha_victorias=racha_local["racha_victorias"],
        racha_sin_perder=racha_local["racha_sin_perder"],
        racha_derrotas=racha_local["racha_derrotas"],
        racha_goles=racha_local["racha_goles"],
        over_2_5_pct=round(tend_local["over_2_5"] * 100, 1),
        btts_pct=round(tend_local["btts"] * 100, 1),
        win_rate_condicion=round(rend_local["win_rate_condicion"] * 100, 1),
        goles_prom_condicion=round(rend_local["goles_prom_condicion"], 2),
    )

    n5v = forma_visitante["partidos"]
    visitante_stats = EstadisticasEquipoResponse(
        nombre=partido.equipo_visitante_nombre,
        ultimos_5=ultimos_visitante,
        victorias_5=int(forma_visitante["victorias"] * n5v) if n5v > 0 else 0,
        empates_5=int(forma_visitante["empates"] * n5v) if n5v > 0 else 0,
        derrotas_5=int(forma_visitante["derrotas"] * n5v) if n5v > 0 else 0,
        goles_favor_prom=round(forma_visitante["goles_favor"], 2),
        goles_contra_prom=round(forma_visitante["goles_contra"], 2),
        clean_sheets_5=int(forma_visitante["clean_sheets"] * n5v) if n5v > 0 else 0,
        racha_victorias=racha_visitante["racha_victorias"],
        racha_sin_perder=racha_visitante["racha_sin_perder"],
        racha_derrotas=racha_visitante["racha_derrotas"],
        racha_goles=racha_visitante["racha_goles"],
        over_2_5_pct=round(tend_visitante["over_2_5"] * 100, 1),
        btts_pct=round(tend_visitante["btts"] * 100, 1),
        win_rate_condicion=round(rend_visitante["win_rate_condicion"] * 100, 1),
        goles_prom_condicion=round(rend_visitante["goles_prom_condicion"], 2),
    )

    return ContextoPrediccionResponse(
        local=local_stats,
        visitante=visitante_stats,
        h2h_total=h2h["total"],
        h2h_wins_local=h2h["wins_local"],
        h2h_empates=h2h["empates"],
        h2h_wins_visitante=h2h["wins_visitante"],
        h2h_goles_prom=round(h2h["goles_prom"], 2),
        h2h_ultimos=h2h["ultimos"],
    )
