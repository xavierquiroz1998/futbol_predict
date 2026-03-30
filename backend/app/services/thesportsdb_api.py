"""
Cliente para TheSportsDB API v1 (complementario).

Cubre amistosos internacionales y otros partidos que Football-Data.org no incluye.
Key compartida gratuita: 123 (sin registro).
Rate limit: ~30 req/min. Usamos una sola conexión reutilizada y delays.
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime

import httpx


class TheSportsDBService:
    BASE_URL = "https://www.thesportsdb.com/api/v1/json/123"

    # Selecciones relevantes para buscar partidos internacionales
    # Cada request toma ~2s de delay, así que limitamos a las más importantes
    SELECCIONES = [
        134507,  # Ecuador
        133914,  # Argentina
        133915,  # Brazil
        133927,  # Colombia
        133939,  # Uruguay
        133913,  # Mexico
        133923,  # England
        134768,  # Spain
        133935,  # France
        133931,  # Italy
    ]

    async def buscar_partidos_por_fecha(self, fecha: date) -> list[dict]:
        """Busca partidos internacionales de fútbol en una fecha."""
        partidos = []
        existing_ids = set()
        fecha_str = fecha.isoformat()

        async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
            for i, team_id in enumerate(self.SELECCIONES):
                if i > 0:
                    await asyncio.sleep(2)

                try:
                    response = await client.get(
                        f"{self.BASE_URL}/eventsnext.php",
                        params={"id": team_id},
                    )
                    if response.status_code == 429:
                        # Rate limited - esperamos y dejamos de buscar más
                        break
                    response.raise_for_status()
                    events = response.json().get("events") or []
                    for e in events:
                        eid = e.get("idEvent")
                        if e.get("dateEvent") == fecha_str and eid not in existing_ids:
                            partidos.append(e)
                            existing_ids.add(eid)
                except Exception:
                    continue

        return partidos


def parsear_partido_thesportsdb(event: dict) -> dict:
    """Convierte un evento de TheSportsDB al formato del modelo Partido."""
    status_raw = event.get("strStatus") or "Not Started"

    status_map = {
        "Not Started": "NS",
        "Match Finished": "FT",
        "FT": "FT",
        "1H": "LIVE",
        "2H": "LIVE",
        "HT": "HT",
        "Postponed": "PST",
        "Cancelled": "CANC",
    }
    status = status_map.get(status_raw, "NS")

    timestamp = event.get("strTimestamp") or ""
    if "T" in timestamp:
        try:
            fecha = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            fecha = datetime.fromisoformat(timestamp)
    else:
        date_str = event.get("dateEvent", "2000-01-01")
        time_str = event.get("strTime", "00:00:00")
        fecha = datetime.fromisoformat(f"{date_str}T{time_str}")

    goles_local = event.get("intHomeScore")
    goles_visitante = event.get("intAwayScore")
    for val_name in ("goles_local", "goles_visitante"):
        val = locals()[val_name]
        if val is not None:
            try:
                locals()[val_name] = int(val)
            except (ValueError, TypeError):
                locals()[val_name] = None

    if goles_local is not None:
        try:
            goles_local = int(goles_local)
        except (ValueError, TypeError):
            goles_local = None
    if goles_visitante is not None:
        try:
            goles_visitante = int(goles_visitante)
        except (ValueError, TypeError):
            goles_visitante = None

    return {
        "api_id": int(event.get("idEvent", 0)),
        "liga_nombre": event.get("strLeague", ""),
        "liga_pais": event.get("strCountry"),
        "liga_logo_url": event.get("strLeagueBadge"),
        "equipo_local_api_id": int(event.get("idHomeTeam", 0)),
        "equipo_local_nombre": event.get("strHomeTeam", ""),
        "equipo_local_logo": event.get("strHomeTeamBadge"),
        "equipo_visitante_api_id": int(event.get("idAwayTeam", 0)),
        "equipo_visitante_nombre": event.get("strAwayTeam", ""),
        "equipo_visitante_logo": event.get("strAwayTeamBadge"),
        "fecha": fecha,
        "estado": status,
        "goles_local": goles_local,
        "goles_visitante": goles_visitante,
        "finalizado": status == "FT",
    }


thesportsdb_api = TheSportsDBService()
