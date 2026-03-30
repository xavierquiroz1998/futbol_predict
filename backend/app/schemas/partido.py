from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class EquipoResponse(BaseModel):
    api_id: int
    nombre: str
    logo_url: str | None = None
    pais: str | None = None

    model_config = {"from_attributes": True}


class PartidoResponse(BaseModel):
    api_id: int
    liga_nombre: str
    liga_pais: str | None = None
    liga_logo_url: str | None = None

    equipo_local_nombre: str
    equipo_local_logo: str | None = None
    equipo_visitante_nombre: str
    equipo_visitante_logo: str | None = None

    fecha: datetime
    estado: str

    goles_local: int | None = None
    goles_visitante: int | None = None
    finalizado: bool

    model_config = {"from_attributes": True}


class PrediccionResponse(BaseModel):
    partido_api_id: int
    prediccion: str
    prob_local: float
    prob_empate: float
    prob_visitante: float
    over_under_pred: str | None = None
    prob_over: float | None = None
    prob_under: float | None = None
    marcador_pred: str | None = None
    btts_pred: bool | None = None
    prob_btts: float | None = None
    resultado_real: str | None = None
    acertada: bool | None = None
    creada_en: datetime

    model_config = {"from_attributes": True}


class EstadisticasEquipoResponse(BaseModel):
    nombre: str
    ultimos_5: str  # ej: "VVDEV"
    victorias_5: int
    empates_5: int
    derrotas_5: int
    goles_favor_prom: float
    goles_contra_prom: float
    clean_sheets_5: int
    racha_victorias: int
    racha_sin_perder: int
    racha_derrotas: int
    racha_goles: int
    over_2_5_pct: float
    btts_pct: float
    win_rate_condicion: float  # local o visitante según corresponda
    goles_prom_condicion: float


class ContextoPrediccionResponse(BaseModel):
    local: EstadisticasEquipoResponse
    visitante: EstadisticasEquipoResponse
    h2h_total: int
    h2h_wins_local: int
    h2h_empates: int
    h2h_wins_visitante: int
    h2h_goles_prom: float
    h2h_ultimos: list[str]  # ej: ["Local 2-1", "Empate 1-1", ...]


class CuotaCasaResponse(BaseModel):
    casa: str
    local: float | None = None
    empate: float | None = None
    visitante: float | None = None


class CuotasMediaResponse(BaseModel):
    local: float | None = None
    empate: float | None = None
    visitante: float | None = None
    prob_local: float | None = None
    prob_empate: float | None = None
    prob_visitante: float | None = None
    over: float | None = None
    under: float | None = None


class CuotasResponse(BaseModel):
    casas: list[CuotaCasaResponse] = []
    media: CuotasMediaResponse | None = None
    total_casas: int = 0
    estimadas: bool = False


class PartidoConPrediccionResponse(BaseModel):
    partido: PartidoResponse
    prediccion: PrediccionResponse | None = None
    contexto: ContextoPrediccionResponse | None = None
    cuotas: CuotasResponse | None = None
