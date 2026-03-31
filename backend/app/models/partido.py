from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Equipo(Base):
    __tablename__ = "equipos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(200))
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pais: Mapped[str | None] = mapped_column(String(100), nullable=True)


class Partido(Base):
    __tablename__ = "partidos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    liga_nombre: Mapped[str] = mapped_column(String(200))
    liga_pais: Mapped[str | None] = mapped_column(String(100), nullable=True)
    liga_logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    equipo_local_api_id: Mapped[int] = mapped_column(Integer, index=True)
    equipo_local_nombre: Mapped[str] = mapped_column(String(200))
    equipo_local_logo: Mapped[str | None] = mapped_column(String(500), nullable=True)

    equipo_visitante_api_id: Mapped[int] = mapped_column(Integer, index=True)
    equipo_visitante_nombre: Mapped[str] = mapped_column(String(200))
    equipo_visitante_logo: Mapped[str | None] = mapped_column(String(500), nullable=True)

    fecha: Mapped[datetime] = mapped_column(DateTime, index=True)
    estado: Mapped[str] = mapped_column(String(20), default="NS")

    goles_local: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goles_visitante: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goles_local_ht: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goles_visitante_ht: Mapped[int | None] = mapped_column(Integer, nullable=True)

    finalizado: Mapped[bool] = mapped_column(Boolean, default=False)


class Prediccion(Base):
    __tablename__ = "predicciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partido_api_id: Mapped[int] = mapped_column(Integer, index=True)

    prediccion: Mapped[str] = mapped_column(String(20))  # "local", "empate", "visitante"
    prob_local: Mapped[float] = mapped_column(Float)
    prob_empate: Mapped[float] = mapped_column(Float)
    prob_visitante: Mapped[float] = mapped_column(Float)

    # Predicciones adicionales
    over_under_pred: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "over", "under"
    prob_over: Mapped[float | None] = mapped_column(Float, nullable=True)
    prob_under: Mapped[float | None] = mapped_column(Float, nullable=True)
    marcador_pred: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "2-1", "1-0", etc
    btts_pred: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    prob_btts: Mapped[float | None] = mapped_column(Float, nullable=True)

    sin_datos: Mapped[bool] = mapped_column(Boolean, default=False)

    resultado_real: Mapped[str | None] = mapped_column(String(20), nullable=True)
    acertada: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    creada_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Cuota(Base):
    __tablename__ = "cuotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    partido_api_id: Mapped[int] = mapped_column(Integer, index=True)
    casa: Mapped[str] = mapped_column(String(100))  # "pinnacle", "bet365", etc.
    mercado: Mapped[str] = mapped_column(String(50))  # "h2h", "totals", "btts"

    cuota_local: Mapped[float | None] = mapped_column(Float, nullable=True)
    cuota_empate: Mapped[float | None] = mapped_column(Float, nullable=True)
    cuota_visitante: Mapped[float | None] = mapped_column(Float, nullable=True)
    cuota_over: Mapped[float | None] = mapped_column(Float, nullable=True)
    cuota_under: Mapped[float | None] = mapped_column(Float, nullable=True)

    actualizada_en: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
