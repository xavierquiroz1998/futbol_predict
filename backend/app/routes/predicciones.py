from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.partido import Partido, Prediccion
from app.schemas.partido import PartidoConPrediccionResponse, PartidoResponse, PrediccionResponse
from app.services.actualizar_resultados import actualizar_y_verificar_pendientes
from app.services.partido_service import obtener_partido_por_api_id
from app.services.predictor import predictor

router = APIRouter()


@router.post("/{partido_api_id}", response_model=PrediccionResponse)
def crear_prediccion(partido_api_id: int, db: Session = Depends(get_db)):
    """Genera una predicción para un partido usando el modelo ML."""
    partido = obtener_partido_por_api_id(db, partido_api_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if partido.finalizado:
        raise HTTPException(status_code=400, detail="El partido ya finalizó")

    # Verificar si ya existe una predicción
    existente = (
        db.query(Prediccion)
        .filter(Prediccion.partido_api_id == partido_api_id)
        .first()
    )
    if existente:
        return PrediccionResponse.model_validate(existente)

    try:
        pred = predictor.predecir_partido(db, partido)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.add(pred)
    db.commit()
    db.refresh(pred)

    return PrediccionResponse.model_validate(pred)


@router.post("/{partido_api_id}/verificar", response_model=PrediccionResponse)
def verificar_prediccion(partido_api_id: int, db: Session = Depends(get_db)):
    """Verifica si la predicción fue acertada comparando con el resultado real."""
    partido = obtener_partido_por_api_id(db, partido_api_id)
    if not partido:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    if not partido.finalizado:
        raise HTTPException(status_code=400, detail="El partido aún no ha finalizado")

    pred = (
        db.query(Prediccion)
        .filter(Prediccion.partido_api_id == partido_api_id)
        .first()
    )
    if not pred:
        raise HTTPException(status_code=404, detail="No hay predicción para este partido")

    pred = predictor.verificar_prediccion(db, pred, partido)
    return PrediccionResponse.model_validate(pred)


@router.get("/historial", response_model=list[PartidoConPrediccionResponse])
def historial_predicciones(
    solo_verificadas: bool = False,
    db: Session = Depends(get_db),
):
    """Obtiene el historial de predicciones con datos del partido."""
    query = db.query(Prediccion)
    if solo_verificadas:
        query = query.filter(Prediccion.acertada.isnot(None))

    resultado = []
    for pred in query.order_by(Prediccion.creada_en.desc()).all():
        partido = db.query(Partido).filter(Partido.api_id == pred.partido_api_id).first()
        if partido:
            resultado.append(PartidoConPrediccionResponse(
                partido=PartidoResponse.model_validate(partido),
                prediccion=PrediccionResponse.model_validate(pred),
            ))
    return resultado


@router.post("/actualizar-resultados")
async def actualizar_resultados(db: Session = Depends(get_db)):
    """Actualiza resultados de partidos finalizados y verifica predicciones pendientes."""
    return await actualizar_y_verificar_pendientes(db)


@router.get("/estadisticas")
def estadisticas_predicciones(db: Session = Depends(get_db)):
    """Devuelve estadísticas de acierto de las predicciones."""
    verificadas = db.query(Prediccion).filter(Prediccion.acertada.isnot(None)).all()

    if not verificadas:
        return {
            "total_predicciones": db.query(Prediccion).count(),
            "verificadas": 0,
            "acertadas": 0,
            "falladas": 0,
            "porcentaje_acierto": 0,
        }

    acertadas = sum(1 for p in verificadas if p.acertada)
    total = len(verificadas)

    return {
        "total_predicciones": db.query(Prediccion).count(),
        "verificadas": total,
        "acertadas": acertadas,
        "falladas": total - acertadas,
        "porcentaje_acierto": round(acertadas / total * 100, 2),
    }
