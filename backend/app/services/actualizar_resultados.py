"""
Servicio para actualizar resultados de partidos ya jugados y verificar predicciones.
Consulta TheSportsDB para obtener marcadores finales.
"""
from __future__ import annotations

import logging

import httpx
from sqlalchemy.orm import Session

from app.models.partido import Partido, Prediccion

logger = logging.getLogger(__name__)

THESPORTSDB_URL = "https://www.thesportsdb.com/api/v1/json/123"


async def actualizar_resultado_partido(db: Session, partido: Partido) -> bool:
    """Actualiza el resultado de un partido consultando TheSportsDB."""
    if partido.finalizado:
        return False

    try:
        async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
            r = await client.get(f"{THESPORTSDB_URL}/lookupevent.php?id={partido.api_id}")
            if r.status_code != 200:
                return False

            events = r.json().get("events") or []
            if not events:
                return False

            event = events[0]
            status = event.get("strStatus", "")
            home_score = event.get("intHomeScore")
            away_score = event.get("intAwayScore")

            if status in ("Match Finished", "FT") and home_score is not None and away_score is not None:
                partido.goles_local = int(home_score)
                partido.goles_visitante = int(away_score)
                partido.estado = "FT"
                partido.finalizado = True
                db.commit()
                logger.info(f"Resultado actualizado: {partido.equipo_local_nombre} {home_score}-{away_score} {partido.equipo_visitante_nombre}")
                return True

    except Exception as e:
        logger.warning(f"Error actualizando resultado de partido {partido.api_id}: {e}")

    return False


async def actualizar_y_verificar_pendientes(db: Session) -> dict:
    """Actualiza resultados de partidos pendientes y verifica predicciones."""
    predicciones_pendientes = db.query(Prediccion).filter(Prediccion.acertada.is_(None)).all()

    actualizados = 0
    verificados = 0
    acertadas = 0

    for pred in predicciones_pendientes:
        partido = db.query(Partido).filter(Partido.api_id == pred.partido_api_id).first()
        if not partido:
            continue

        # Si no está finalizado, intentar actualizar
        if not partido.finalizado:
            updated = await actualizar_resultado_partido(db, partido)
            if updated:
                actualizados += 1

        # Si ahora está finalizado, verificar predicción
        if partido.finalizado:
            if partido.goles_local > partido.goles_visitante:
                resultado = "local"
            elif partido.goles_local < partido.goles_visitante:
                resultado = "visitante"
            else:
                resultado = "empate"

            pred.resultado_real = resultado
            pred.acertada = pred.prediccion == resultado
            verificados += 1
            if pred.acertada:
                acertadas += 1

    db.commit()

    return {
        "predicciones_pendientes": len(predicciones_pendientes),
        "resultados_actualizados": actualizados,
        "predicciones_verificadas": verificados,
        "acertadas": acertadas,
    }
