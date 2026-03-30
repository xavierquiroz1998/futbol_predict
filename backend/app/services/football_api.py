"""
Cliente para Football-Data.org API v4.

Documentación: https://docs.football-data.org/general/v4/index.html
Plan gratuito: 10 req/min, 12 competiciones.

Competiciones gratuitas:
    PL  - Premier League
    BL1 - Bundesliga
    SA  - Serie A
    PD  - La Liga
    FL1 - Ligue 1
    CL  - Champions League
    ELC - Championship
    PPL - Primeira Liga
    DED - Eredivisie
    BSA - Série A (Brasil)
    WC  - World Cup
    EC  - European Championship
"""
from __future__ import annotations

from datetime import date

import httpx

from app.config import settings


# Mapeo de códigos de competición a IDs numéricos (para BD)
COMPETITION_IDS = {
    "PL": 2021, "BL1": 2002, "SA": 2019, "PD": 2014,
    "FL1": 2015, "CL": 2001, "ELC": 2016, "PPL": 2017,
    "DED": 2003, "BSA": 2013, "WC": 2000, "EC": 2018,
}


class FootballDataService:
    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self):
        self.headers = {
            "X-Auth-Token": settings.football_data_api_key,
        }

    async def _get(self, endpoint: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient(verify=False) as client:
            response = await client.get(
                f"{self.BASE_URL}/{endpoint}",
                headers=self.headers,
                params=params or {},
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

    async def obtener_partidos_por_fecha(self, fecha: date | None = None) -> list[dict]:
        """Obtiene los partidos de una fecha específica."""
        if fecha is None:
            fecha = date.today()

        fecha_str = fecha.isoformat()
        data = await self._get("matches", params={
            "dateFrom": fecha_str,
            "dateTo": fecha_str,
        })
        return data.get("matches", [])

    async def obtener_partidos_rango(self, desde: date, hasta: date) -> list[dict]:
        """Obtiene partidos en un rango de fechas."""
        data = await self._get("matches", params={
            "dateFrom": desde.isoformat(),
            "dateTo": hasta.isoformat(),
        })
        return data.get("matches", [])

    async def obtener_partido_por_id(self, match_id: int) -> dict | None:
        """Obtiene un partido específico por su ID."""
        try:
            data = await self._get(f"matches/{match_id}")
            return data
        except httpx.HTTPStatusError:
            return None

    async def obtener_partidos_competicion(
        self, competition_code: str, season: int | None = None, status: str | None = None
    ) -> list[dict]:
        """Obtiene partidos de una competición.

        Args:
            competition_code: Código de competición (PL, BL1, SA, PD, FL1, CL, etc.)
            season: Año de la temporada (ej: 2024 para 2024/25)
            status: SCHEDULED, TIMED, IN_PLAY, PAUSED, FINISHED, etc.
        """
        params = {}
        if season:
            params["season"] = season
        if status:
            params["status"] = status

        data = await self._get(f"competitions/{competition_code}/matches", params=params)
        return data.get("matches", [])

    async def obtener_clasificacion(self, competition_code: str, season: int | None = None) -> dict:
        """Obtiene la clasificación/tabla de una competición."""
        params = {}
        if season:
            params["season"] = season
        return await self._get(f"competitions/{competition_code}/standings", params=params)

    async def obtener_equipo(self, team_id: int) -> dict | None:
        """Obtiene información de un equipo."""
        try:
            return await self._get(f"teams/{team_id}")
        except httpx.HTTPStatusError:
            return None

    async def obtener_head_to_head(self, match_id: int, limit: int = 10) -> list[dict]:
        """Obtiene enfrentamientos directos a partir de un partido."""
        try:
            data = await self._get(f"matches/{match_id}/head2head", params={"limit": limit})
            return data.get("aggregates", {}).get("matches", [])
        except httpx.HTTPStatusError:
            return []

    async def obtener_partidos_historicos(
        self, competition_code: str, season: int
    ) -> list[dict]:
        """Obtiene todos los partidos finalizados de una competición y temporada."""
        return await self.obtener_partidos_competicion(
            competition_code, season=season, status="FINISHED"
        )


football_api = FootballDataService()
