"""
Script de entrenamiento del modelo de predicción.

Uso:
    python -m app.ml.train

Requiere datos históricos en la BD (ejecutar primero recolectar_historicos.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from app.database import SessionLocal
from app.ml.features import FEATURE_COLUMNS, generar_features, obtener_partidos_como_df

MODEL_DIR = Path(__file__).parent
MODEL_PATH = MODEL_DIR / "model.pkl"
ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"
METRICS_PATH = MODEL_DIR / "metrics.json"


def entrenar():
    print("=" * 60)
    print("ENTRENAMIENTO DEL MODELO DE PREDICCIÓN")
    print("=" * 60)

    # 1. Obtener datos
    print("\n1. Obteniendo datos de la BD...")
    db = SessionLocal()
    try:
        df_raw = obtener_partidos_como_df(db)
    finally:
        db.close()

    if df_raw.empty:
        print("ERROR: No hay partidos en la BD. Ejecuta primero:")
        print("  python -m app.scripts.recolectar_historicos --todas --temporada 2024")
        return

    print(f"   Partidos cargados: {len(df_raw)}")

    # 2. Generar features
    print("\n2. Generando features...")
    df = generar_features(df_raw)
    print(f"   Muestras con features: {len(df)}")

    if len(df) < 50:
        print("ERROR: Insuficientes datos para entrenar (mínimo 50 muestras).")
        return

    # 3. Preparar datos
    print("\n3. Preparando datos...")
    X = df[FEATURE_COLUMNS].values
    y_labels = df["resultado"].values

    le = LabelEncoder()
    y = le.fit_transform(y_labels)

    print(f"   Clases: {dict(zip(le.classes_, np.bincount(y)))}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"   Train: {len(X_train)}, Test: {len(X_test)}")

    # 4. Entrenar modelo
    print("\n4. Entrenando XGBoost...")

    # Calcular pesos para balancear clases (el empate está subrepresentado)
    from collections import Counter
    counts = Counter(y_train)
    total = len(y_train)
    n_classes = len(counts)
    sample_weights = np.array([total / (n_classes * counts[yi]) for yi in y_train])
    print(f"   Pesos por clase: { {le.inverse_transform([k])[0]: round(total/(n_classes*v), 2) for k,v in counts.items()} }")

    model = XGBClassifier(
        n_estimators=300,
        max_depth=5,
        learning_rate=0.08,
        subsample=0.8,
        colsample_bytree=0.7,
        min_child_weight=3,
        gamma=0.1,
        random_state=42,
        eval_metric="mlogloss",
    )
    model.fit(X_train, y_train, sample_weight=sample_weights)

    # 5. Evaluar
    print("\n5. Evaluación:")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n   Accuracy: {accuracy:.4f}")
    print(f"\n   Classification Report:")
    report = classification_report(y_test, y_pred, target_names=le.classes_)
    print(report)

    print("   Confusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"   {cm}")

    # Cross-validation
    print("\n   Cross-validation (5-fold):")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="accuracy")
    print(f"   Scores: {cv_scores.round(4)}")
    print(f"   Media: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    # 6. Feature importance
    print("\n6. Feature Importance (top 10):")
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:10]
    for i, idx in enumerate(indices):
        print(f"   {i+1}. {FEATURE_COLUMNS[idx]}: {importances[idx]:.4f}")

    # 7. Guardar modelo
    print("\n7. Guardando modelo...")
    joblib.dump(model, MODEL_PATH)
    joblib.dump(le, ENCODER_PATH)

    metrics = {
        "accuracy": float(accuracy),
        "cv_mean": float(cv_scores.mean()),
        "cv_std": float(cv_scores.std()),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "classes": le.classes_.tolist(),
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"   Modelo guardado en: {MODEL_PATH}")
    print(f"   Encoder guardado en: {ENCODER_PATH}")
    print(f"   Métricas guardadas en: {METRICS_PATH}")
    print("\nEntrenamiento completado.")


if __name__ == "__main__":
    entrenar()
