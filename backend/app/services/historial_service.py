"""
Servicio de historial on-demand.

Cuando se genera una predicción, busca automáticamente el historial reciente
de ambos equipos y lo almacena en la BD para calcular features.

Fuentes:
- Football-Data.org: equipos de las 12 ligas cubiertas (10 partidos por equipo)
- TheSportsDB: cualquier equipo del mundo (últimos resultados + temporada)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.partido import Partido

logger = logging.getLogger(__name__)


async def _buscar_historial_footballdata(
    client: httpx.AsyncClient, team_id: int
) -> list[dict]:
    """Busca últimos partidos de un equipo en Football-Data.org."""
    if not settings.football_data_api_key:
        return []

    try:
        r = await client.get(
            f"https://api.football-data.org/v4/teams/{team_id}/matches",
            headers={"X-Auth-Token": settings.football_data_api_key},
            params={"status": "FINISHED", "limit": 15},
        )
        if r.status_code != 200:
            return []

        matches = r.json().get("matches", [])
        resultados = []
        for m in matches:
            score = m.get("score", {})
            ft = score.get("fullTime", {})
            ht = score.get("halfTime", {})
            resultados.append({
                "api_id": m["id"],
                "fecha": datetime.fromisoformat(m["utcDate"].replace("Z", "+00:00")),
                "liga": m.get("competition", {}).get("name", ""),
                "liga_pais": m.get("area", {}).get("name"),
                "local_id": m["homeTeam"]["id"],
                "local_nombre": m["homeTeam"]["name"],
                "local_logo": m["homeTeam"].get("crest"),
                "visitante_id": m["awayTeam"]["id"],
                "visitante_nombre": m["awayTeam"]["name"],
                "visitante_logo": m["awayTeam"].get("crest"),
                "goles_local": ft.get("home"),
                "goles_visitante": ft.get("away"),
                "goles_local_ht": ht.get("home"),
                "goles_visitante_ht": ht.get("away"),
            })
        return resultados

    except Exception as e:
        logger.warning(f"Error Football-Data.org historial team {team_id}: {e}")
        return []


async def _buscar_historial_thesportsdb(
    client: httpx.AsyncClient, team_id: int, liga_id: str | None = None
) -> list[dict]:
    """Busca últimos partidos de un equipo en TheSportsDB."""
    resultados = []

    try:
        # 1. Último resultado
        r = await client.get(
            f"https://www.thesportsdb.com/api/v1/json/123/eventslast.php?id={team_id}"
        )
        if r.status_code == 200:
            events = r.json().get("results") or []
            for e in events:
                if e.get("intHomeScore") is not None:
                    try:
                        resultados.append(_parsear_evento_tsdb(e))
                    except (ValueError, TypeError):
                        continue

        await asyncio.sleep(2)  # Rate limit

        # 2. Eventos de la temporada actual si tenemos liga
        if liga_id:
            for season in ["2026", "2025-2026", "2025"]:
                r2 = await client.get(
                    f"https://www.thesportsdb.com/api/v1/json/123/eventsseason.php?id={liga_id}&s={season}"
                )
                if r2.status_code == 200:
                    events2 = r2.json().get("events") or []
                    team_events = [
                        e for e in events2
                        if (str(e.get("idHomeTeam")) == str(team_id) or str(e.get("idAwayTeam")) == str(team_id))
                        and e.get("intHomeScore") is not None
                    ]
                    for e in team_events:
                        try:
                            parsed = _parsear_evento_tsdb(e)
                            if not any(r["api_id"] == parsed["api_id"] for r in resultados):
                                resultados.append(parsed)
                        except (ValueError, TypeError):
                            continue
                    if team_events:
                        break  # Ya encontramos la temporada correcta
                await asyncio.sleep(2)

    except Exception as e:
        logger.warning(f"Error TheSportsDB historial team {team_id}: {e}")

    return resultados


def _parsear_evento_tsdb(e: dict) -> dict:
    """Parsea un evento de TheSportsDB a formato de partido."""
    gl = int(e["intHomeScore"])
    gv = int(e["intAwayScore"])

    timestamp = e.get("strTimestamp") or e.get("dateEvent", "")
    if "T" in timestamp:
        try:
            fecha = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            fecha = datetime.fromisoformat(timestamp)
    else:
        fecha = datetime.fromisoformat(f"{e['dateEvent']}T00:00:00")

    return {
        "api_id": int(e["idEvent"]),
        "fecha": fecha,
        "liga": e.get("strLeague", ""),
        "liga_pais": e.get("strCountry"),
        "local_id": int(e.get("idHomeTeam", 0)),
        "local_nombre": e.get("strHomeTeam", ""),
        "local_logo": e.get("strHomeTeamBadge"),
        "visitante_id": int(e.get("idAwayTeam", 0)),
        "visitante_nombre": e.get("strAwayTeam", ""),
        "visitante_logo": e.get("strAwayTeamBadge"),
        "goles_local": gl,
        "goles_visitante": gv,
        "goles_local_ht": None,
        "goles_visitante_ht": None,
    }


def _guardar_en_bd(db: Session, partidos_data: list[dict]):
    """Guarda partidos en la BD si no existen."""
    nuevos = 0
    for datos in partidos_data:
        existente = db.query(Partido).filter(Partido.api_id == datos["api_id"]).first()
        if not existente:
            partido = Partido(
                api_id=datos["api_id"],
                liga_nombre=datos["liga"],
                liga_pais=datos.get("liga_pais"),
                equipo_local_api_id=datos["local_id"],
                equipo_local_nombre=datos["local_nombre"],
                equipo_local_logo=datos.get("local_logo"),
                equipo_visitante_api_id=datos["visitante_id"],
                equipo_visitante_nombre=datos["visitante_nombre"],
                equipo_visitante_logo=datos.get("visitante_logo"),
                fecha=datos["fecha"],
                estado="FT",
                goles_local=datos["goles_local"],
                goles_visitante=datos["goles_visitante"],
                goles_local_ht=datos.get("goles_local_ht"),
                goles_visitante_ht=datos.get("goles_visitante_ht"),
                finalizado=True,
            )
            db.add(partido)
            nuevos += 1
    if nuevos > 0:
        db.commit()
    return nuevos


async def obtener_historial_equipo(
    db: Session, team_api_id: int, liga_id_tsdb: str | None = None
) -> int:
    """Busca y almacena historial de un equipo. Retorna cantidad de partidos nuevos."""
    # Verificar si ya tenemos suficientes datos
    partidos_existentes = db.query(Partido).filter(
        (Partido.equipo_local_api_id == team_api_id) | (Partido.equipo_visitante_api_id == team_api_id)
    ).filter(Partido.finalizado == True).count()

    if partidos_existentes >= 10:
        return 0  # Ya tenemos suficiente

    async with httpx.AsyncClient(verify=False, timeout=15) as client:
        # Intentar Football-Data.org primero (más datos, más rápido)
        resultados = await _buscar_historial_footballdata(client, team_api_id)

        if len(resultados) < 5:
            # Complementar con TheSportsDB
            resultados_tsdb = await _buscar_historial_thesportsdb(client, team_api_id, liga_id_tsdb)
            existing_ids = {r["api_id"] for r in resultados}
            for r in resultados_tsdb:
                if r["api_id"] not in existing_ids:
                    resultados.append(r)

    nuevos = _guardar_en_bd(db, resultados)
    logger.info(f"Historial equipo {team_api_id}: {nuevos} partidos nuevos ({len(resultados)} encontrados)")
    return nuevos
