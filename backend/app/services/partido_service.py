"""
Servicio de partidos. Combina Football-Data.org y TheSportsDB para máxima cobertura.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.partido import Partido
from app.services.football_api import football_api
from app.services.thesportsdb_api import (
    parsear_partido_thesportsdb,
    thesportsdb_api,
)

logger = logging.getLogger(__name__)

# Mapeo de estados Football-Data.org
STATUS_MAP = {
    "SCHEDULED": "NS",
    "TIMED": "NS",
    "IN_PLAY": "LIVE",
    "PAUSED": "HT",
    "FINISHED": "FT",
    "SUSPENDED": "SUSP",
    "POSTPONED": "PST",
    "CANCELLED": "CANC",
    "AWARDED": "AWD",
}

# Cache simple para no repetir sincronización TheSportsDB en la misma sesión
_tsdb_sincronizado: dict[str, bool] = {}


def _parsear_partido_footballdata(match: dict) -> dict:
    """Convierte la respuesta de Football-Data.org al formato del modelo Partido."""
    competition = match.get("competition", {})
    area = match.get("area", {})
    home = match.get("homeTeam", {})
    away = match.get("awayTeam", {})
    score = match.get("score", {})
    full_time = score.get("fullTime", {})
    status_raw = match.get("status", "SCHEDULED")
    status = STATUS_MAP.get(status_raw, status_raw)

    return {
        "api_id": match["id"],
        "liga_nombre": competition.get("name", ""),
        "liga_pais": area.get("name"),
        "liga_logo_url": competition.get("emblem"),
        "equipo_local_api_id": home.get("id", 0),
        "equipo_local_nombre": home.get("name", ""),
        "equipo_local_logo": home.get("crest"),
        "equipo_visitante_api_id": away.get("id", 0),
        "equipo_visitante_nombre": away.get("name", ""),
        "equipo_visitante_logo": away.get("crest"),
        "fecha": datetime.fromisoformat(match["utcDate"].replace("Z", "+00:00")),
        "estado": status,
        "goles_local": full_time.get("home"),
        "goles_visitante": full_time.get("away"),
        "finalizado": status_raw == "FINISHED",
    }


def _upsert_partido(db: Session, datos: dict) -> Partido:
    """Inserta o actualiza un partido en la BD."""
    partido = db.query(Partido).filter(Partido.api_id == datos["api_id"]).first()
    if partido:
        for key, value in datos.items():
            setattr(partido, key, value)
    else:
        partido = Partido(**datos)
        db.add(partido)
    return partido


async def sincronizar_partidos_del_dia(db: Session, fecha: date | None = None) -> list[Partido]:
    """Obtiene partidos del día desde ambas APIs y los sincroniza con la BD."""
    if fecha is None:
        fecha = date.today()

    partidos = []
    fecha_str = fecha.isoformat()

    # 1. Football-Data.org (rápido, ~1s)
    try:
        fixtures_fd = await football_api.obtener_partidos_por_fecha(fecha)
        for fixture in fixtures_fd:
            datos = _parsear_partido_footballdata(fixture)
            partido = _upsert_partido(db, datos)
            partidos.append(partido)
        logger.info(f"Football-Data.org: {len(fixtures_fd)} partidos para {fecha}")
    except Exception as e:
        logger.warning(f"Error Football-Data.org: {e}")

    # 2. TheSportsDB (lento por rate limit, solo si no se hizo ya)
    if fecha_str not in _tsdb_sincronizado:
        try:
            fixtures_tsdb = await thesportsdb_api.buscar_partidos_por_fecha(fecha)
            api_ids_existentes = {p.api_id for p in partidos}
            nuevos = 0
            for event in fixtures_tsdb:
                datos = parsear_partido_thesportsdb(event)
                if datos["api_id"] not in api_ids_existentes:
                    partido = _upsert_partido(db, datos)
                    partidos.append(partido)
                    nuevos += 1
            _tsdb_sincronizado[fecha_str] = True
            logger.info(f"TheSportsDB: {nuevos} partidos adicionales para {fecha}")
        except Exception as e:
            logger.warning(f"Error TheSportsDB: {e}")
    else:
        # Ya sincronizado, solo agregar de BD lo que TheSportsDB puso antes
        db_partidos = obtener_partidos_por_fecha_db(db, fecha)
        api_ids_existentes = {p.api_id for p in partidos}
        for p in db_partidos:
            if p.api_id not in api_ids_existentes:
                partidos.append(p)

    if partidos:
        db.commit()

    return partidos


async def sincronizar_thesportsdb(db: Session, fecha: date) -> list[Partido]:
    """Sincroniza solo TheSportsDB para una fecha (llamada manual)."""
    partidos = []
    try:
        fixtures_tsdb = await thesportsdb_api.buscar_partidos_por_fecha(fecha)
        for event in fixtures_tsdb:
            datos = parsear_partido_thesportsdb(event)
            partido = _upsert_partido(db, datos)
            partidos.append(partido)
        if partidos:
            db.commit()
        _tsdb_sincronizado[fecha.isoformat()] = True
        logger.info(f"TheSportsDB sync manual: {len(partidos)} partidos para {fecha}")
    except Exception as e:
        logger.warning(f"Error TheSportsDB sync: {e}")
    return partidos


def obtener_partidos_por_fecha_db(db: Session, fecha: date) -> list[Partido]:
    """Obtiene partidos de una fecha desde la BD."""
    inicio = datetime(fecha.year, fecha.month, fecha.day, 0, 0, 0)
    fin = datetime(fecha.year, fecha.month, fecha.day, 23, 59, 59)
    return db.query(Partido).filter(Partido.fecha.between(inicio, fin)).all()


def obtener_partido_por_api_id(db: Session, api_id: int) -> Partido | None:
    """Obtiene un partido por su api_id."""
    return db.query(Partido).filter(Partido.api_id == api_id).first()
