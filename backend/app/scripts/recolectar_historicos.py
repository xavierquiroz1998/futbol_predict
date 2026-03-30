"""
Script para recolectar datos históricos de partidos finalizados.

Usa Football-Data.org API v4.

Uso:
    python -m app.scripts.recolectar_historicos --liga PL --temporada 2024
    python -m app.scripts.recolectar_historicos --todas --temporada 2024

Competiciones disponibles (plan gratuito):
    PL  - Premier League (Inglaterra)
    PD  - La Liga (España)
    SA  - Serie A (Italia)
    BL1 - Bundesliga (Alemania)
    FL1 - Ligue 1 (Francia)
    CL  - Champions League

Nota: Football-Data.org tiene límite de 10 req/min en plan gratuito.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime

from app.database import SessionLocal
from app.models.partido import Partido
from app.services.football_api import football_api
from app.services.partido_service import _parsear_partido_footballdata as _parsear_partido

LIGAS_PRINCIPALES = {
    "PL": "Premier League",
    "PD": "La Liga",
    "SA": "Serie A",
    "BL1": "Bundesliga",
    "FL1": "Ligue 1",
}


async def recolectar(liga_code: str, temporada: int):
    print(f"Recolectando datos: {LIGAS_PRINCIPALES.get(liga_code, liga_code)}, Temporada {temporada}")

    fixtures = await football_api.obtener_partidos_historicos(liga_code, temporada)
    print(f"  Partidos encontrados: {len(fixtures)}")

    db = SessionLocal()
    nuevos = 0
    actualizados = 0

    try:
        for fixture in fixtures:
            datos = _parsear_partido(fixture)
            partido = db.query(Partido).filter(Partido.api_id == datos["api_id"]).first()

            if partido:
                for key, value in datos.items():
                    setattr(partido, key, value)
                actualizados += 1
            else:
                partido = Partido(**datos)
                db.add(partido)
                nuevos += 1

        db.commit()
        print(f"  Nuevos: {nuevos}, Actualizados: {actualizados}")
    finally:
        db.close()


async def recolectar_todas_las_ligas(temporada: int):
    for liga_code in LIGAS_PRINCIPALES:
        await recolectar(liga_code, temporada)
        print("  Esperando 7s (rate limit 10 req/min)...")
        await asyncio.sleep(7)


def main():
    parser = argparse.ArgumentParser(description="Recolectar datos históricos de partidos")
    parser.add_argument("--liga", type=str, help="Código de la liga (ej: PL, PD, SA, BL1, FL1)")
    parser.add_argument("--temporada", type=int, required=True, help="Año de la temporada (ej: 2024)")
    parser.add_argument("--todas", action="store_true", help="Recolectar de las 5 ligas principales")

    args = parser.parse_args()

    if args.todas:
        asyncio.run(recolectar_todas_las_ligas(args.temporada))
    elif args.liga:
        asyncio.run(recolectar(args.liga, args.temporada))
    else:
        print("Debes especificar --liga CODIGO o --todas")
        print("Códigos: PL, PD, SA, BL1, FL1")
        sys.exit(1)


if __name__ == "__main__":
    main()
