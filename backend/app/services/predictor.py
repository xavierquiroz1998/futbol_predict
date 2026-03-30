"""
Servicio de predicción: resultado, over/under, BTTS y marcador probable.
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

# Marcadores más comunes en fútbol con probabilidades base
MARCADORES_COMUNES = [
    "1-0", "0-0", "1-1", "2-1", "2-0", "0-1", "1-2", "0-2",
    "3-1", "2-2", "3-0", "0-3", "3-2", "1-3", "2-3", "4-0",
    "4-1", "0-4", "4-2", "3-3",
]


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

    def _calcular_features(self, db: Session, partido: Partido) -> np.ndarray:
        """Calcula las features para un partido."""
        df = obtener_partidos_como_df(db)
        if df.empty:
            raise ValueError("No hay datos históricos para generar predicción")

        local_id = partido.equipo_local_api_id
        visitante_id = partido.equipo_visitante_api_id
        fecha = partido.fecha

        forma_local_5 = _forma_reciente(df, local_id, fecha, n=5)
        forma_visitante_5 = _forma_reciente(df, visitante_id, fecha, n=5)
        forma_local_10 = _forma_reciente(df, local_id, fecha, n=10)
        forma_visitante_10 = _forma_reciente(df, visitante_id, fecha, n=10)
        racha_local = _racha_actual(df, local_id, fecha)
        racha_visitante = _racha_actual(df, visitante_id, fecha)
        tend_local = _tendencia_goles(df, local_id, fecha)
        tend_visitante = _tendencia_goles(df, visitante_id, fecha)
        rend_local = _rendimiento_local_visitante(df, local_id, fecha, es_local=True)
        rend_visitante = _rendimiento_local_visitante(df, visitante_id, fecha, es_local=False)
        h2h = _head_to_head(df, local_id, visitante_id, fecha)

        features = np.array([[
            forma_local_5["victorias"], forma_local_5["empates"], forma_local_5["derrotas"],
            forma_local_5["goles_favor"], forma_local_5["goles_contra"],
            forma_local_5["puntos"], forma_local_5["clean_sheets"],
            forma_visitante_5["victorias"], forma_visitante_5["empates"], forma_visitante_5["derrotas"],
            forma_visitante_5["goles_favor"], forma_visitante_5["goles_contra"],
            forma_visitante_5["puntos"], forma_visitante_5["clean_sheets"],
            forma_local_10["puntos"], forma_local_10["goles_favor"], forma_local_10["goles_contra"],
            forma_visitante_10["puntos"], forma_visitante_10["goles_favor"], forma_visitante_10["goles_contra"],
            racha_local["racha_victorias"], racha_local["racha_sin_perder"],
            racha_local["racha_derrotas"], racha_local["racha_goles"],
            racha_visitante["racha_victorias"], racha_visitante["racha_sin_perder"],
            racha_visitante["racha_derrotas"], racha_visitante["racha_goles"],
            tend_local["over_2_5"], tend_local["btts"], tend_local["goles_total_prom"],
            tend_visitante["over_2_5"], tend_visitante["btts"], tend_visitante["goles_total_prom"],
            rend_local["win_rate_condicion"], rend_local["goles_prom_condicion"], rend_local["gc_prom_condicion"],
            rend_visitante["win_rate_condicion"], rend_visitante["goles_prom_condicion"], rend_visitante["gc_prom_condicion"],
            h2h["h2h_win_local"], h2h["h2h_empates"], h2h["h2h_win_visitante"], h2h["h2h_goles_prom"],
            forma_local_5["puntos"] - forma_visitante_5["puntos"],
            forma_local_10["puntos"] - forma_visitante_10["puntos"],
            forma_local_5["goles_favor"] - forma_visitante_5["goles_favor"],
            forma_local_5["goles_contra"] - forma_visitante_5["goles_contra"],
            racha_local["racha_victorias"] - racha_visitante["racha_victorias"],
        ]])

        # Guardar tendencias para over/under y BTTS
        self._last_tendencias = {
            "local_gf": forma_local_5["goles_favor"],
            "local_gc": forma_local_5["goles_contra"],
            "visitante_gf": forma_visitante_5["goles_favor"],
            "visitante_gc": forma_visitante_5["goles_contra"],
            "local_over": tend_local["over_2_5"],
            "visitante_over": tend_visitante["over_2_5"],
            "local_btts": tend_local["btts"],
            "visitante_btts": tend_visitante["btts"],
            "local_goles_total": tend_local["goles_total_prom"],
            "visitante_goles_total": tend_visitante["goles_total_prom"],
            "local_gf_casa": rend_local["goles_prom_condicion"],
            "visitante_gf_fuera": rend_visitante["goles_prom_condicion"],
            "local_gc_casa": rend_local["gc_prom_condicion"],
            "visitante_gc_fuera": rend_visitante["gc_prom_condicion"],
            "h2h_goles_prom": h2h["h2h_goles_prom"],
        }

        return features

    def _predecir_over_under(self) -> tuple[str, float, float]:
        """Predice over/under 2.5 basado en tendencias de goles."""
        t = self._last_tendencias

        # Promedio ponderado de goles esperados
        goles_esperados_local = (t["local_gf"] + t["local_gf_casa"]) / 2
        goles_esperados_visitante = (t["visitante_gf"] + t["visitante_gf_fuera"]) / 2
        total_esperado = goles_esperados_local + goles_esperados_visitante

        # Factor over basado en tendencia de ambos equipos
        over_factor = (t["local_over"] + t["visitante_over"]) / 2

        # Combinar
        if total_esperado > 2.5:
            prob_over = 0.5 + (total_esperado - 2.5) * 0.15 + over_factor * 0.2
        else:
            prob_over = 0.5 - (2.5 - total_esperado) * 0.15 + over_factor * 0.2

        prob_over = max(0.1, min(0.9, prob_over))
        prob_under = 1 - prob_over

        pred = "over" if prob_over > 0.5 else "under"
        return pred, prob_over, prob_under

    def _predecir_btts(self) -> tuple[bool, float]:
        """Predice si ambos equipos anotarán."""
        t = self._last_tendencias
        btts_factor = (t["local_btts"] + t["visitante_btts"]) / 2

        # Probabilidad de que el local anote (contra la defensa visitante)
        prob_local_anota = min(0.95, t["local_gf_casa"] / max(t["local_gf_casa"] + 0.5, 1))
        prob_visitante_anota = min(0.95, t["visitante_gf_fuera"] / max(t["visitante_gf_fuera"] + 0.5, 1))

        prob_btts = btts_factor * 0.5 + (prob_local_anota * prob_visitante_anota) * 0.5
        prob_btts = max(0.1, min(0.9, prob_btts))

        return prob_btts > 0.5, prob_btts

    def _predecir_marcador(self, prob_local: float, prob_empate: float, prob_visitante: float) -> str:
        """Predice el marcador más probable basado en goles esperados."""
        t = self._last_tendencias

        goles_local_esp = (t["local_gf"] + t["local_gf_casa"]) / 2
        goles_visitante_esp = (t["visitante_gf"] + t["visitante_gf_fuera"]) / 2

        # Ajustar según la defensa rival
        goles_local_esp = (goles_local_esp + t["visitante_gc_fuera"]) / 2
        goles_visitante_esp = (goles_visitante_esp + t["local_gc_casa"]) / 2

        # Redondear a enteros más cercanos
        gl = max(0, round(goles_local_esp))
        gv = max(0, round(goles_visitante_esp))

        # Ajustar según predicción de resultado
        if prob_local > prob_empate and prob_local > prob_visitante:
            if gl <= gv:
                gl = gv + 1
        elif prob_visitante > prob_empate and prob_visitante > prob_local:
            if gv <= gl:
                gv = gl + 1
        else:  # empate
            gl = gv = max(gl, gv, 1)
            if gl > 3:
                gl = gv = 1

        return f"{gl}-{gv}"

    def predecir_partido(self, db: Session, partido: Partido) -> Prediccion:
        """Genera predicción completa: resultado, over/under, BTTS, marcador."""
        self._cargar_modelo()

        features = self._calcular_features(db, partido)

        # Predicción de resultado
        proba = self._model.predict_proba(features)[0]
        clase_idx = np.argmax(proba)
        prediccion_label = self._encoder.inverse_transform([clase_idx])[0]

        clases = self._encoder.classes_
        prob_dict = dict(zip(clases, proba))
        pl = float(prob_dict.get("local", 0))
        pe = float(prob_dict.get("empate", 0))
        pv = float(prob_dict.get("visitante", 0))

        # Predicciones adicionales
        over_pred, prob_over, prob_under = self._predecir_over_under()
        btts_pred, prob_btts = self._predecir_btts()
        marcador = self._predecir_marcador(pl, pe, pv)

        pred = Prediccion(
            partido_api_id=partido.api_id,
            prediccion=prediccion_label,
            prob_local=pl,
            prob_empate=pe,
            prob_visitante=pv,
            over_under_pred=over_pred,
            prob_over=prob_over,
            prob_under=prob_under,
            marcador_pred=marcador,
            btts_pred=btts_pred,
            prob_btts=prob_btts,
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
