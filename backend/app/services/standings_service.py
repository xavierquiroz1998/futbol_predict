"""
Servicio de clasificaciones. Obtiene posición, puntos y stats de equipos en sus ligas.
Se usa como feature adicional para el modelo de predicción.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from app.services.football_api import football_api

logger = logging.getLogger(__name__)

# Cache de standings para no hacer requests repetidos
_standings_cache: dict[str, dict] = {}
_cache_timestamp: dict[str, datetime] = {}
CACHE_TTL = timedelta(hours=6)


async def obtener_standings_equipo(competition_code: str, team_id: int, season: int | None = None) -> dict | None:
    """Obtiene la posición y stats de un equipo en su liga."""
    cache_key = f"{competition_code}_{season}"

    # Verificar cache
    if cache_key in _standings_cache:
        if datetime.utcnow() - _cache_timestamp.get(cache_key, datetime.min) < CACHE_TTL:
            return _standings_cache[cache_key].get(team_id)

    try:
        data = await football_api.obtener_clasificacion(competition_code, season)
        standings = data.get("standings", [])

        team_map = {}
        for standing in standings:
            if standing.get("type") == "TOTAL":
                for entry in standing.get("table", []):
                    tid = entry["team"]["id"]
                    team_map[tid] = {
                        "posicion": entry["position"],
                        "puntos": entry["points"],
                        "partidos_jugados": entry["playedGames"],
                        "victorias": entry["won"],
                        "empates": entry["draw"],
                        "derrotas": entry["lost"],
                        "goles_favor": entry["goalsFor"],
                        "goles_contra": entry["goalsAgainst"],
                        "diferencia_goles": entry["goalDifference"],
                        "forma": entry.get("form", ""),
                    }

        _standings_cache[cache_key] = team_map
        _cache_timestamp[cache_key] = datetime.utcnow()

        return team_map.get(team_id)

    except Exception as e:
        logger.warning(f"Error obteniendo standings {competition_code}: {e}")
        return None


# Mapeo de nombre de liga a código de competición
LIGA_TO_CODE = {
    "Premier League": "PL",
    "La Liga": "PD",
    "Primera Division": "PD",
    "Serie A": "SA",
    "Bundesliga": "BL1",
    "Ligue 1": "FL1",
    "Championship": "ELC",
    "Champions League": "CL",
    "UEFA Champions League": "CL",
    "Primeira Liga": "PPL",
    "Eredivisie": "DED",
    "Campeonato Brasileiro Série A": "BSA",
}
