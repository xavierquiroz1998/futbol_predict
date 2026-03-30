"""
Servicio de cuotas de apuestas usando The Odds API.

https://the-odds-api.com
Plan gratuito: 500 requests/mes.
Devuelve cuotas de múltiples casas de apuestas para calcular promedios.

Sport keys relevantes:
    soccer_epl          - Premier League
    soccer_spain_la_liga - La Liga
    soccer_italy_serie_a - Serie A
    soccer_germany_bundesliga - Bundesliga
    soccer_france_ligue_one - Ligue 1
    soccer_uefa_champs_league - Champions League
    soccer_colombia_primera_a - Liga Colombia
    soccer_brazil_serie_a - Brasileirão
    soccer_conmebol_libertadores - Copa Libertadores
"""
from __future__ import annotations

import logging
from datetime import datetime

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models.partido import Cuota

logger = logging.getLogger(__name__)

# Mapeo de nombre de liga a sport_key de The Odds API
LIGA_TO_SPORT_KEY = {
    "Premier League": "soccer_epl",
    "La Liga": "soccer_spain_la_liga",
    "Primera Division": "soccer_spain_la_liga",
    "Serie A": "soccer_italy_serie_a",
    "Bundesliga": "soccer_germany_bundesliga",
    "Ligue 1": "soccer_france_ligue_one",
    "Champions League": "soccer_uefa_champs_league",
    "UEFA Champions League": "soccer_uefa_champs_league",
    "Colombia Categoría Primera A": "soccer_colombia_primera_a",
    "Campeonato Brasileiro Série A": "soccer_brazil_serie_a",
    "Copa Libertadores": "soccer_conmebol_libertadores",
    "Championship": "soccer_efl_champ",
}

# Mapeo inverso: nombre de equipo normalizado para matching
def _normalizar(nombre: str) -> str:
    """Normaliza nombre de equipo para comparar entre APIs."""
    reemplazos = {
        " FC": "", " CF": "", " SC": "", " AC": "",
        "AFC ": "", "Club ": "", "Deportivo ": "",
        "Independiente ": "", "Atlético ": "Atletico ",
    }
    n = nombre.strip()
    for old, new in reemplazos.items():
        n = n.replace(old, new)
    return n.lower().strip()


class OddsService:
    BASE_URL = "https://api.the-odds-api.com/v4"

    async def obtener_cuotas_liga(self, sport_key: str) -> list[dict]:
        """Obtiene cuotas de todos los partidos próximos de una liga."""
        if not settings.odds_api_key:
            return []

        try:
            async with httpx.AsyncClient(verify=False, timeout=15.0) as client:
                # Cuotas 1X2
                r = await client.get(
                    f"{self.BASE_URL}/sports/{sport_key}/odds",
                    params={
                        "apiKey": settings.odds_api_key,
                        "regions": "eu",
                        "markets": "h2h,totals",
                        "oddsFormat": "decimal",
                    },
                )
                if r.status_code == 401:
                    logger.warning("Odds API: API key inválida")
                    return []
                if r.status_code == 403:
                    logger.warning("Odds API: Acceso bloqueado (posible firewall/proxy corporativo)")
                    return []
                if r.status_code == 429:
                    logger.warning("Odds API: Rate limit alcanzado")
                    return []
                r.raise_for_status()

                remaining = r.headers.get("x-requests-remaining", "?")
                logger.info(f"Odds API: {sport_key} OK (requests restantes: {remaining})")
                return r.json()

        except Exception as e:
            logger.warning(f"Error Odds API ({sport_key}): {e}")
            return []

    def _match_partido(self, odds_event: dict, equipo_local: str, equipo_visitante: str) -> bool:
        """Verifica si un evento de odds coincide con un partido."""
        home_odds = _normalizar(odds_event.get("home_team", ""))
        away_odds = _normalizar(odds_event.get("away_team", ""))
        home_local = _normalizar(equipo_local)
        away_local = _normalizar(equipo_visitante)

        return (
            (home_odds in home_local or home_local in home_odds)
            and (away_odds in away_local or away_local in away_odds)
        )

    async def obtener_cuotas_partido(
        self, db: Session, partido_api_id: int, liga_nombre: str,
        equipo_local: str, equipo_visitante: str
    ) -> dict | None:
        """Obtiene y almacena cuotas para un partido específico."""
        # Verificar si ya tenemos cuotas recientes
        cuotas_existentes = (
            db.query(Cuota)
            .filter(Cuota.partido_api_id == partido_api_id)
            .all()
        )
        if cuotas_existentes:
            return self._calcular_medias(cuotas_existentes)

        # Buscar sport_key
        sport_key = None
        for nombre, key in LIGA_TO_SPORT_KEY.items():
            if nombre.lower() in liga_nombre.lower() or liga_nombre.lower() in nombre.lower():
                sport_key = key
                break

        if not sport_key:
            return None

        # Obtener cuotas de la liga
        eventos = await self.obtener_cuotas_liga(sport_key)
        if not eventos:
            return None

        # Buscar el partido
        evento_match = None
        for evento in eventos:
            if self._match_partido(evento, equipo_local, equipo_visitante):
                evento_match = evento
                break

        if not evento_match:
            return None

        # Guardar cuotas por casa de apuestas
        for bookmaker in evento_match.get("bookmakers", []):
            casa = bookmaker.get("title", bookmaker.get("key", "unknown"))

            for market in bookmaker.get("markets", []):
                mercado = market.get("key", "")
                outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}

                cuota = Cuota(
                    partido_api_id=partido_api_id,
                    casa=casa,
                    mercado=mercado,
                    actualizada_en=datetime.utcnow(),
                )

                if mercado == "h2h":
                    cuota.cuota_local = outcomes.get(evento_match["home_team"])
                    cuota.cuota_empate = outcomes.get("Draw")
                    cuota.cuota_visitante = outcomes.get(evento_match["away_team"])
                elif mercado == "totals":
                    cuota.cuota_over = outcomes.get("Over")
                    cuota.cuota_under = outcomes.get("Under")

                db.add(cuota)

        db.commit()

        # Recalcular con las nuevas cuotas
        cuotas = db.query(Cuota).filter(Cuota.partido_api_id == partido_api_id).all()
        return self._calcular_medias(cuotas)

    def _calcular_medias(self, cuotas: list[Cuota]) -> dict:
        """Calcula la media de cuotas de todas las casas de apuestas."""
        h2h = [c for c in cuotas if c.mercado == "h2h" and c.cuota_local is not None]
        totals = [c for c in cuotas if c.mercado == "totals" and c.cuota_over is not None]

        resultado = {
            "casas": [],
            "media": {},
            "total_casas": 0,
        }

        if h2h:
            resultado["total_casas"] = len(h2h)
            resultado["media"]["local"] = round(sum(c.cuota_local for c in h2h) / len(h2h), 2)
            resultado["media"]["empate"] = round(sum(c.cuota_empate for c in h2h) / len(h2h), 2)
            resultado["media"]["visitante"] = round(sum(c.cuota_visitante for c in h2h) / len(h2h), 2)

            # Convertir cuotas a probabilidades implícitas
            total_inv = (1/resultado["media"]["local"] + 1/resultado["media"]["empate"] + 1/resultado["media"]["visitante"])
            resultado["media"]["prob_local"] = round((1/resultado["media"]["local"]) / total_inv * 100, 1)
            resultado["media"]["prob_empate"] = round((1/resultado["media"]["empate"]) / total_inv * 100, 1)
            resultado["media"]["prob_visitante"] = round((1/resultado["media"]["visitante"]) / total_inv * 100, 1)

            # Detalle por casa
            for c in h2h:
                resultado["casas"].append({
                    "casa": c.casa,
                    "local": c.cuota_local,
                    "empate": c.cuota_empate,
                    "visitante": c.cuota_visitante,
                })

        if totals:
            resultado["media"]["over"] = round(sum(c.cuota_over for c in totals) / len(totals), 2)
            resultado["media"]["under"] = round(sum(c.cuota_under for c in totals) / len(totals), 2)

        return resultado


    def calcular_cuotas_estimadas(self, prob_local: float, prob_empate: float, prob_visitante: float) -> dict:
        """Calcula cuotas estimadas a partir de las probabilidades del modelo ML.
        Se usa como fallback cuando no hay cuotas reales disponibles."""
        margin = 1.05  # Margen típico de casa de apuestas (5%)

        cuota_local = round(margin / max(prob_local, 0.01), 2)
        cuota_empate = round(margin / max(prob_empate, 0.01), 2)
        cuota_visitante = round(margin / max(prob_visitante, 0.01), 2)

        return {
            "casas": [],
            "media": {
                "local": cuota_local,
                "empate": cuota_empate,
                "visitante": cuota_visitante,
                "prob_local": round(prob_local * 100, 1),
                "prob_empate": round(prob_empate * 100, 1),
                "prob_visitante": round(prob_visitante * 100, 1),
            },
            "total_casas": 0,
            "estimadas": True,
        }


odds_service = OddsService()
