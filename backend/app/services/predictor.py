"""
Servicio de predicción que usa el modelo entrenado para predecir resultados.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.ml.features import (
    FEATURE_COLUMNS,
    _forma_reciente,
    _head_to_head,
    _racha_actual,
    _rendimiento_local_visitante,
    _tendencia_goles,
    obtener_partidos_como_df,
)
from app.models.partido import Partido, Prediccion

MODEL_DIR = Path(__file__).parent.parent / "ml"
MODEL_PATH = MODEL_DIR / "model.pkl"
ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"


class PredictorService:
    def __init__(self):
        self._model = None
        self._encoder = None

    def _cargar_modelo(self):
        if self._model is None:
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    "Modelo no encontrado. Ejecuta primero: python -m app.ml.train"
                )
            self._model = joblib.load(MODEL_PATH)
            self._encoder = joblib.load(ENCODER_PATH)

    def predecir_partido(self, db: Session, partido: Partido) -> Prediccion:
        """Genera una predicción para un partido dado."""
        self._cargar_modelo()

        df = obtener_partidos_como_df(db)
        if df.empty:
            raise ValueError("No hay datos históricos para generar predicción")

        local_id = partido.equipo_local_api_id
        visitante_id = partido.equipo_visitante_api_id
        fecha = partido.fecha

        # Forma reciente 5 y 10
        forma_local_5 = _forma_reciente(df, local_id, fecha, n=5)
        forma_visitante_5 = _forma_reciente(df, visitante_id, fecha, n=5)
        forma_local_10 = _forma_reciente(df, local_id, fecha, n=10)
        forma_visitante_10 = _forma_reciente(df, visitante_id, fecha, n=10)

        # Rachas
        racha_local = _racha_actual(df, local_id, fecha)
        racha_visitante = _racha_actual(df, visitante_id, fecha)

        # Tendencia goles
        tend_local = _tendencia_goles(df, local_id, fecha)
        tend_visitante = _tendencia_goles(df, visitante_id, fecha)

        # Rendimiento local/visitante
        rend_local = _rendimiento_local_visitante(df, local_id, fecha, es_local=True)
        rend_visitante = _rendimiento_local_visitante(df, visitante_id, fecha, es_local=False)

        # Head to head
        h2h = _head_to_head(df, local_id, visitante_id, fecha)

        features = np.array([[
            # Forma 5
            forma_local_5["victorias"], forma_local_5["empates"], forma_local_5["derrotas"],
            forma_local_5["goles_favor"], forma_local_5["goles_contra"],
            forma_local_5["puntos"], forma_local_5["clean_sheets"],
            forma_visitante_5["victorias"], forma_visitante_5["empates"], forma_visitante_5["derrotas"],
            forma_visitante_5["goles_favor"], forma_visitante_5["goles_contra"],
            forma_visitante_5["puntos"], forma_visitante_5["clean_sheets"],
            # Forma 10
            forma_local_10["puntos"], forma_local_10["goles_favor"], forma_local_10["goles_contra"],
            forma_visitante_10["puntos"], forma_visitante_10["goles_favor"], forma_visitante_10["goles_contra"],
            # Rachas
            racha_local["racha_victorias"], racha_local["racha_sin_perder"],
            racha_local["racha_derrotas"], racha_local["racha_goles"],
            racha_visitante["racha_victorias"], racha_visitante["racha_sin_perder"],
            racha_visitante["racha_derrotas"], racha_visitante["racha_goles"],
            # Tendencia goles
            tend_local["over_2_5"], tend_local["btts"], tend_local["goles_total_prom"],
            tend_visitante["over_2_5"], tend_visitante["btts"], tend_visitante["goles_total_prom"],
            # Rendimiento local/visitante
            rend_local["win_rate_condicion"], rend_local["goles_prom_condicion"], rend_local["gc_prom_condicion"],
            rend_visitante["win_rate_condicion"], rend_visitante["goles_prom_condicion"], rend_visitante["gc_prom_condicion"],
            # H2H
            h2h["h2h_win_local"], h2h["h2h_empates"], h2h["h2h_win_visitante"], h2h["h2h_goles_prom"],
            # Diferenciales
            forma_local_5["puntos"] - forma_visitante_5["puntos"],
            forma_local_10["puntos"] - forma_visitante_10["puntos"],
            forma_local_5["goles_favor"] - forma_visitante_5["goles_favor"],
            forma_local_5["goles_contra"] - forma_visitante_5["goles_contra"],
            racha_local["racha_victorias"] - racha_visitante["racha_victorias"],
        ]])

        # Predicción
        proba = self._model.predict_proba(features)[0]
        clase_idx = np.argmax(proba)
        prediccion_label = self._encoder.inverse_transform([clase_idx])[0]

        clases = self._encoder.classes_
        prob_dict = dict(zip(clases, proba))

        pred = Prediccion(
            partido_api_id=partido.api_id,
            prediccion=prediccion_label,
            prob_local=float(prob_dict.get("local", 0)),
            prob_empate=float(prob_dict.get("empate", 0)),
            prob_visitante=float(prob_dict.get("visitante", 0)),
            creada_en=datetime.utcnow(),
        )

        return pred

    def verificar_prediccion(self, db: Session, prediccion: Prediccion, partido: Partido) -> Prediccion:
        if not partido.finalizado:
            return prediccion

        if partido.goles_local > partido.goles_visitante:
            resultado_real = "local"
        elif partido.goles_local < partido.goles_visitante:
            resultado_real = "visitante"
        else:
            resultado_real = "empate"

        prediccion.resultado_real = resultado_real
        prediccion.acertada = prediccion.prediccion == resultado_real
        db.commit()

        return prediccion


predictor = PredictorService()
