from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.partido import Prediccion
from app.schemas.partido import (
    PartidoConPrediccionResponse,
    PartidoResponse,
    PrediccionResponse,
)
from app.services.contexto_service import generar_contexto
from app.services.partido_service import (
    obtener_partido_por_api_id,
    obtener_partidos_por_fecha_db,
    sincronizar_partidos_del_dia,
    sincronizar_thesportsdb,
)

router = APIRouter()


@router.get("/hoy", response_model=list[PartidoConPrediccionResponse])
async def partidos_hoy(db: Session = Depends(get_db)):
    """Obtiene los partidos de hoy, sincronizando con la API externa."""
    hoy = date.today()
    try:
        partidos = await sincronizar_partidos_del_dia(db, hoy)
    except Exception as e:
        logger.warning(f"Error al sincronizar con API externa: {e}")
        partidos = obtener_partidos_por_fecha_db(db, hoy)

    resultado = []
    for partido in partidos:
        prediccion = (
            db.query(Prediccion)
            .filter(Prediccion.partido_api_id == partido.api_id)
            .first()
        )
        resultado.append(
            PartidoConPrediccionResponse(
                partido=PartidoResponse.model_validate(partido),
                prediccion=PrediccionResponse.model_validate(prediccion) if prediccion else None,
            )
        )

    return resultado


@router.get("/fecha/{fecha}", response_model=list[PartidoConPrediccionResponse])
async def partidos_por_fecha(
    fecha: date,
    sincronizar: bool = Query(False, description="Si True, sincroniza con la API externa"),
    db: Session = Depends(get_db),
):
    """Obtiene los partidos de una fecha específica."""
    if sincronizar:
        try:
            partidos = await sincronizar_partidos_del_dia(db, fecha)
        except Exception as e:
            logger.warning(f"Error al sincronizar con API externa: {e}")
            partidos = obtener_partidos_por_fecha_db(db, fecha)
    else:
        partidos = obtener_partidos_por_fecha_db(db, fecha)

    resultado = []
    for partido in partidos:
        prediccion = (
            db.query(Prediccion)
            .filter(Prediccion.partido_api_id == partido.api_id)
            .first()
        )
        resultado.append(
            PartidoConPrediccionResponse(
                partido=PartidoResponse.model_validate(partido),
                prediccion=PrediccionResponse.model_validate(prediccion) if prediccion else None,
            )
        )

    return resultado


@router.post("/sincronizar/{fecha}")
async def sincronizar_fecha(fecha: date, db: Session = Depends(get_db)):
    """Sincroniza partidos internacionales (TheSportsDB) para una fecha. Tarda ~20s."""
    partidos = await sincronizar_thesportsdb(db, fecha)
    return {"sincronizados": len(partidos), "fecha": fecha.isoformat()}


@router.get("/{api_id}", response_model=PartidoConPrediccionResponse)
async def obtener_partido(api_id: int, db: Session = Depends(get_db)):
    """Obtiene un partido específico con su predicción."""
    partido = obtener_partido_por_api_id(db, api_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    prediccion = (
        db.query(Prediccion)
        .filter(Prediccion.partido_api_id == api_id)
        .first()
    )

    contexto = generar_contexto(db, partido)

    return PartidoConPrediccionResponse(
        partido=PartidoResponse.model_validate(partido),
        prediccion=PrediccionResponse.model_validate(prediccion) if prediccion else None,
        contexto=contexto,
    )


@router.get("/{api_id}/resultado", response_model=PartidoResponse)
async def obtener_resultado(api_id: int, db: Session = Depends(get_db)):
    """Obtiene el resultado de un partido ya jugado."""
    partido = obtener_partido_por_api_id(db, api_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if not partido.finalizado:
        raise HTTPException(status_code=400, detail="El partido aún no ha finalizado")

    return PartidoResponse.model_validate(partido)
